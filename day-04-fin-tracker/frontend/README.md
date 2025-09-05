# 💰 Personal Finance Tracker - Streamlit Frontend

A beautiful and intuitive Streamlit chatbot interface for your personal finance tracking application powered by Parlant AI.

## 🚀 Features

### 💬 Interactive Chat Interface
- Natural language conversation with your finance bot
- Real-time responses from Parlant AI backend
- Clean, user-friendly design with proper message formatting

### 🎯 Quick Action Buttons
- **Start Data Gathering**: Begin financial data collection
- **Add Income**: Record income sources
- **Add Expenses**: Track spending by category
- **Add Loan Payments**: Record debt payments
- **Get Summary**: View financial overview
- **Check Status**: See data collection progress

### 📊 Smart Categories
- 🏠 Housing (rent, mortgage, utilities)
- 🍔 Food (groceries, dining)
- 🚗 Transportation (gas, car payments)
- 🏥 Healthcare (insurance, medical)
- 🎬 Entertainment (movies, subscriptions)
- ⚡ Utilities (electricity, internet)
- 💳 Debt (loans, credit cards)

### 🔧 Built-in Tools
- Backend connection status checker
- Chat history management
- Responsive design for all devices
- Privacy-focused local data handling

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
cd frontend
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

### 3. Run the Streamlit App
```bash
cd frontend
streamlit run streamlit_app.py
```

### 4. Access the Application
- Open your browser to: `http://localhost:8501`
- The backend API runs on: `http://localhost:8000`

## 💡 How to Use

### Getting Started
1. Click "🚀 Start Data Gathering" or type "start data gathering"
2. Follow the guided process to add your financial information
3. Use natural language like:
   - "I earn $5000 monthly from my job"
   - "I spend $1200 on rent"
   - "I pay $300 for car loan"

### Quick Commands
- `start data gathering` - Begin tracking your finances
- `get expense summary` - View your financial summary
- `get data status` - Check collection progress
- `help` - Get assistance and guidance

### Example Conversations
```
You: "I want to track my finances"
Bot: "Started financial data collection! Let's gather your income sources first..."

You: "I earn $5000 monthly from my job"
Bot: "Recorded income: $5000 monthly from job"

You: "I spend $1200 on rent and $300 on groceries"
Bot: "Recorded $1200 expense for housing and $300 for food"

You: "What's my summary?"
Bot: "💰 Total Income: $5000, 💸 Total Expenses: $1500, Net: $3500"
```

## 🔒 Privacy & Security

- All data is processed locally
- No personal information is shared externally
- Data is stored only during your session
- For tracking purposes only, not financial advice

## 🎨 Features Included

### User Interface
- ✅ Clean, modern design
- ✅ Responsive layout
- ✅ Real-time chat interface
- ✅ Quick action sidebar
- ✅ Status indicators
- ✅ Message formatting

### Functionality
- ✅ Backend API integration
- ✅ Error handling
- ✅ Connection status checking
- ✅ Chat history management
- ✅ Natural language processing
- ✅ Category-based expense tracking

### User Experience
- ✅ Welcome message and guidance
- ✅ Quick action buttons
- ✅ Help documentation
- ✅ Clear instructions
- ✅ Visual feedback
- ✅ Auto-scrolling chat

## 🔧 Technical Details

- **Frontend**: Streamlit with custom CSS styling
- **Backend**: FastAPI with Parlant AI
- **Communication**: REST API calls
- **Styling**: Custom CSS for enhanced UI
- **Responsive**: Works on desktop and mobile

## 🚨 Troubleshooting

### Backend Connection Issues
1. Make sure the backend server is running on port 8000
2. Check the backend URL in the Streamlit app
3. Use the "🔄 Check Backend Status" button

### Common Solutions
- Restart both frontend and backend servers
- Check that all dependencies are installed
- Ensure ports 8000 and 8501 are available

## 📱 Mobile Friendly

The interface is fully responsive and works great on:
- 💻 Desktop computers
- 📱 Mobile phones
- 📟 Tablets

## 🎯 Next Steps

After setup, you can:
1. Start tracking your finances immediately
2. Use natural language to add financial data
3. Get real-time summaries and insights
4. Export your data for further analysis

Happy financial tracking! 💰✨
