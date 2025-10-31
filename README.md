# 📋 Table of Contents

* [About](#-about)
* [Features](#-features)
* [Demo](#-demo)
* [Tech Stack](#️-tech-stack)
* [Getting Started](#-getting-started)

  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
  * [Running the Application](#running-the-application)
* [Usage](#-usage)
* [Project Structure](#-project-structure)
* [Contributing](#-contributing)
* [License](#-license)
* [Contact](#-contact)

---

## 🎯 About

**HireReady** is a comprehensive platform designed to help job seekers prepare for interviews, track applications, and improve their chances of landing their dream job. Whether you're a fresh graduate or an experienced professional, HireReady provides the tools and resources you need to succeed in your job search.

---

## ✨ Features

* **Interview Practice** – Practice with commonly asked interview questions across different domains
* **Resume Builder** – Create professional resumes with customizable templates
* **Application Tracker** – Keep track of all your job applications in one place
* **Mock Interviews** – Simulate real interview scenarios with AI-powered feedback
* **Company Insights** – Get detailed information about companies and their interview processes
* **Progress Analytics** – Track your preparation progress with detailed analytics
* **Resource Library** – Access curated learning materials and preparation guides

---

## 🎥 Demo

<!-- Add your demo link or screenshot here -->

**[Live Demo](#)** | **[Video Walkthrough](#)**
![Show Image](screenshots/demo.png)

---

## 🛠️ Tech Stack

### **Frontend**

* React.js / Next.js
* Tailwind CSS
* Redux / Context API

### **Backend**

* Node.js
* Express.js
* MongoDB / PostgreSQL

### **Additional Tools**

* JWT for authentication
* Bcrypt for password hashing
* Axios for API calls

---

## 🚀 Getting Started

### **Prerequisites**

Before you begin, ensure you have the following installed:

* Node.js (v14 or higher)
* npm or yarn
* MongoDB / PostgreSQL (depending on your database choice)

---

### **Installation**

**1. Clone the repository**

```bash
git clone https://github.com/HarshHadiya04/HireReady.git
cd HireReady
```

**2. Install dependencies for the backend**

```bash
cd backend
npm install
```

**3. Install dependencies for the frontend**

```bash
cd ../frontend
npm install
```

**4. Create environment variables**

Create a `.env` file in the backend directory:

```env
PORT=5000
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret
NODE_ENV=development
```

Create a `.env.local` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:5000
```

---

### **Running the Application**

**Start the backend server**

```bash
cd backend
npm start
```

**Start the frontend development server**

```bash
cd frontend
npm start
```

The application should now be running on:
👉 [http://localhost:3000](http://localhost:3000)

---

## 📖 Usage

1. **Sign Up / Login** – Create an account or login to access all features
2. **Complete Your Profile** – Add your skills, experience, and preferences
3. **Start Practicing** – Choose interview questions based on your target role
4. **Track Applications** – Add companies you've applied to and track their status
5. **Analyze Progress** – Review your performance metrics and improvement areas

---

## 📁 Project Structure

```
HireReady/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── utils/
│   │   ├── styles/
│   │   └── App.js
│   └── package.json
├── backend/
│   ├── config/
│   ├── controllers/
│   ├── models/
│   ├── routes/
│   ├── middleware/
│   └── server.js
├── screenshots/
└── README.md
```

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

**Harsh Hadiya** – [@HarshHadiya04](https://github.com/HarshHadiya04)
**Om Hirvania** – [@omhirvania123](https://github.com/omhirvania123)

📎 **Project Link:** [https://github.com/HarshHadiya04/HireReady](https://github.com/HarshHadiya04/HireReady)

---

## 🙏 Acknowledgments

* [React Documentation](https://react.dev/)
* [Node.js Documentation](https://nodejs.org/en/docs)
* [MongoDB Documentation](https://www.mongodb.com/docs/)
* [Tailwind CSS](https://tailwindcss.com/)
* [Lucide Icons](https://lucide.dev/)
