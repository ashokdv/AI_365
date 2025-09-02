import streamlit as st
import requests
import time
from PIL import Image
import io


st.set_page_config(page_title="Image Chat (streaming)", layout="wide")


def init_state():
	if 'messages' not in st.session_state:
		st.session_state['messages'] = []
	if 'endpoint' not in st.session_state:
		st.session_state['endpoint'] = 'http://localhost:8000/upload_stream'


init_state()


## Sidebar: configuration
with st.sidebar:
	st.header('Backend config')
	endpoint = st.text_input('Streaming endpoint (HTTP)', value=st.session_state['endpoint'])
	auth_header = st.text_input('Authorization header (optional)', value='', type='password')
	timeout = st.number_input('Request timeout (seconds)', value=60, min_value=5, step=5)
	simulate = st.checkbox('Simulate streaming locally (no backend)', value=False)
	if endpoint != st.session_state['endpoint']:
		st.session_state['endpoint'] = endpoint


st.title('Image Chat (streaming)')

col1, col2 = st.columns([1, 3])

with col1:
	st.subheader('Input')
	# compact upload button with camera emoji
	uploaded = st.file_uploader('📷 Upload', type=['png', 'jpg', 'jpeg'])
	prompt = st.text_input('Say something (optional)', value='Describe this image in one sentence')
	# inline send button
	send_col1, send_col2 = st.columns([3,1])
	with send_col2:
		send = st.button('Send')

with col2:
	st.subheader('Chat')
	chat_placeholder = st.empty()


def render_chat():
	# Clear and render the entire chat inside a single placeholder so updates replace content
	with chat_placeholder.container():
		for msg in st.session_state['messages']:
			role = msg.get('role', 'assistant')
			content = msg.get('content', '')
			image_bytes = msg.get('image_bytes')
			# Use Streamlit chat if available, otherwise fall back to markdown
			try:
				with st.chat_message(role):
					if image_bytes is not None:
						img = Image.open(io.BytesIO(image_bytes))
						st.image(img, width=140)
					st.write(content)
			except Exception:
				if role == 'user':
					st.markdown('**User**:')
				else:
					st.markdown('**Assistant**:')
				if image_bytes is not None:
					img = Image.open(io.BytesIO(image_bytes))
					st.image(img, width=140)
				st.write(content)


# render_chat()


def stream_from_backend(endpoint, files, data, headers, timeout_sec, placeholder, on_chunk=None):
	"""Send multipart request and stream response lines/chunks back.

	This supports plain chunked text, simple "data: <chunk>" SSE lines and a final "[DONE]" sentinel.
	"""
	try:
		with requests.post(endpoint, files=files or None, data=data or None, headers=headers or None, stream=True, timeout=timeout_sec) as resp:
			resp.raise_for_status()
			full = ''
			for raw in resp.iter_lines(decode_unicode=True):
				if raw is None:
					continue
				line = raw.strip()
				if not line:
					continue
				# SSE style: "data: ..."
				if line.startswith('data:'):
					payload = line[len('data:'):].strip()
				else:
					payload = line

				# try to parse JSON payload that contains fields like {"response": "...", "done": false}
				try:
					import json as _json
					obj = _json.loads(payload)
				except Exception:
					# fallback: treat payload as raw text
					obj = None

				# handle error messages from backend
				if isinstance(obj, dict) and 'error' in obj:
					placeholder.markdown(f"**Error from backend:** {obj.get('error')}")
					return None

				# if we parsed JSON and it has a 'response' field, append it
				piece = ''
				done = False
				if isinstance(obj, dict):
					piece = obj.get('response', '') or ''
					done = bool(obj.get('done', False))
				else:
					# not JSON, treat payload as plain chunk
					piece = payload

				if piece:
					full += piece
					# call on_chunk if provided so caller can update session state
					if callable(on_chunk):
						try:
							on_chunk(piece, done)
						except Exception:
							pass
					else:
						placeholder.markdown(full)

				if done:
					break

			return full
	except requests.exceptions.RequestException as e:
		placeholder.markdown(f'**Error while streaming:** {e}')
		return None


def simulate_stream(text, placeholder, delay=0.06):
	out = ''
	for ch in text:
		out += ch
		placeholder.markdown(out)
		time.sleep(delay)
	return out


if send:
	if not uploaded and not prompt:
		st.warning('Please upload an image or enter a prompt.')
	else:
		# Add user message to chat
		user_msg = {'role': 'user', 'content': prompt or '(image only)'}
		if uploaded:
			uploaded.seek(0)
			user_msg['image_bytes'] = uploaded.read()
		st.session_state['messages'].append(user_msg)

		# Add assistant placeholder and remember its index so we can update in place
		assistant_msg = {'role': 'assistant', 'content': ''}
		if uploaded:
			assistant_msg['image_bytes'] = user_msg.get('image_bytes')
		st.session_state['messages'].append(assistant_msg)
		assistant_index = len(st.session_state['messages']) - 1

		# Re-render chat so user sees their message + empty assistant bubble
		# render_chat()

		# placeholder (to show streaming text while updating session state)
		placeholder = st.empty()

		if simulate:
			sample = "This is a simulated streaming caption: " + (prompt or 'a sample image')
			final = simulate_stream(sample, placeholder)
			# commit final
			st.session_state['messages'][-1]['content'] = final
		else:
			# prepare files and headers
			files = None
			data = {'prompt': prompt}
			headers = {}
			if auth_header:
				headers['Authorization'] = auth_header
			if uploaded:
				uploaded.seek(0)
				files = {'file': (uploaded.name, uploaded.read(), uploaded.type)}
			# stream
			with st.spinner('Waiting for backend stream...'):
				# Stream and update the assistant message in session state chunk-by-chunk
				def on_stream_chunk(chunk_text, done_flag=False):
					# append chunk to assistant content and re-render the chat in-place
					st.session_state['messages'][assistant_index]['content'] += chunk_text
					render_chat()

				# modified streaming function that writes directly using on_stream_chunk
				final = None
				# stream_from_backend will still return the full text, but we'll also update incrementally
				final = stream_from_backend(st.session_state['endpoint'], files, data, headers, timeout, placeholder, on_chunk=on_stream_chunk)
			if final is None:
				st.session_state['messages'][assistant_index]['content'] = '**Error receiving response**'
			else:
				st.session_state['messages'][assistant_index]['content'] = final

		# final render
		render_chat()

