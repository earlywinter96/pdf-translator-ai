"use client";

export default function TestButton() {
  const handleClick = () => {
    alert("TEST BUTTON WORKS!");
    console.log("Test button clicked!");
  };

  return (
    <button 
      onClick={handleClick}
      style={{ background: 'red', color: 'white', padding: '20px' }}
    >
      TEST BUTTON - CLICK ME
    </button>
  );
}