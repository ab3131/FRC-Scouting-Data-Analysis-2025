import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Link, Routes, useNavigate } from 'react-router-dom';
import './Menu.css'
import Button from '@mui/material/Button';
function Menu() {
  const navigate = useNavigate();
  //navigation for Generate button 
  const handleClick = () => {

    
  };
  const handleLoginClick = () => {
    navigate('/')
    
    
  };
  const renderMenu = () => {
    if(localStorage.getItem('username')){
      return <>
        <div className = "myheader">
          <Link to = "/" className = "websiteLink">
            <h1 className = "websiteHeader">Team 2367 Scouting</h1>
          </Link>
        </div>
      </>
    }
    else{
      return(
      <>
        <div className = "myheader">
          <Link to = "/" className = "websiteLink">
            <h1 className = "websiteHeader">Team 2367 Scouting</h1>
          </Link>
        </div>
      </>
      )
    }

  
  }
  return (
    
    <>
    {renderMenu()}
    </>
  )
}

export default Menu