export default function TestApp() {
  return (
    <div style={{ 
      backgroundColor: 'black', 
      color: 'green', 
      minHeight: '100vh', 
      padding: '20px',
      fontFamily: 'monospace' 
    }}>
      <h1>🚀 React is Working!</h1>
      <p>If you can see this, React is mounting correctly.</p>
      <p>Time: {new Date().toLocaleTimeString()}</p>
    </div>
  )
}