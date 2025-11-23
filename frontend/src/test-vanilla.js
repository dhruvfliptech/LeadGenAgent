console.log('=== VANILLA JS TEST ===');
console.log('Document ready state:', document.readyState);
console.log('Body exists:', document.body);
console.log('Root element:', document.getElementById('root'));

// Create a simple test element
const testDiv = document.createElement('div');
testDiv.style.cssText = 'background: black; color: lime; padding: 50px; font-size: 30px; font-family: monospace;';
testDiv.innerHTML = '<h1>VANILLA JS WORKS!</h1><p>If you see this, JavaScript is executing.</p>';

// Try to append to root or body
const root = document.getElementById('root');
if (root) {
  console.log('Appending to root...');
  root.appendChild(testDiv);
} else {
  console.log('Root not found, appending to body...');
  document.body.appendChild(testDiv);
}

console.log('=== TEST COMPLETE ===');