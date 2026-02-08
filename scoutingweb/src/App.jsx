import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Generate from './pages/Generate';
import Menu from './Menu'
import React from 'react'


function App() {
  return (
    <>
    <Router>
      <Menu />
      <Routes>
        <Route path='/' element={<Generate />} />
      </Routes>
    </Router>
    </>
  );
}

export default App;
