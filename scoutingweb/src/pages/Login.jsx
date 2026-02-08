import React, { useState } from 'react';
import './Login.css';
import { BrowserRouter as Router, Route, Link, Routes, useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField'


function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  const handleClick = () => {
    navigate('/Generate');
    
  };

  
  return (
    <>
        <TextField
                id="outlined-basic"
                label="Username"
                variant="outlined"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
        <TextField
                id="outlined-basic"
                label="Password"
                variant="outlined"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
        
        <Button variant="outlined" onClick={() => {handleClick()}}><strong>Login</strong></Button> 

    </>    

  )
}

export default Login