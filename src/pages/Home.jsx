import React, { useEffect, useState } from 'react'
import axios from 'axios'

function Home() {
  const [message, setMessage] = useState('Loading...')

  useEffect(() => {
    axios.get(`${import.meta.env.VITE_MUFASA_API}/`)
      .then(res => setMessage(res.data.message))
      .catch(err => setMessage('Error connecting to API: ' + err.message))
  }, [])

  return (
    <div style={{
      backgroundColor: '#111',
      color: '#fff',
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      flexDirection: 'column',
      fontFamily: 'sans-serif'
    }}>
      <h1>Prince of Pan-Africa 🌍</h1>
      <p>{message}</p>
    </div>
  )
}

export default Home
