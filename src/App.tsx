import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    
    <form className="flex flex-col space-y-4">
      <label>Upload file here:  
        <input type="file" />
      </label>
      
      <button type="submit">Generate Subtitles</button>
    </form>
  )
}

export default App
