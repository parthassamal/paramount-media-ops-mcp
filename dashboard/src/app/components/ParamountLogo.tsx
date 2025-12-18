import React from 'react';

export const ParamountLogo: React.FC<{ className?: string }> = ({ className = "" }) => {
  return (
    <svg 
      className={className} 
      viewBox="0 0 200 60" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Mountain Logo */}
      <g>
        {/* Mountain Peak */}
        <path
          d="M30 5 L50 35 L40 35 L30 20 L20 35 L10 35 Z"
          fill="currentColor"
        />
        {/* Stars */}
        <circle cx="25" cy="15" r="1.5" fill="currentColor" />
        <circle cx="35" cy="15" r="1.5" fill="currentColor" />
        <circle cx="20" cy="22" r="1" fill="currentColor" />
        <circle cx="40" cy="22" r="1" fill="currentColor" />
        <circle cx="30" cy="10" r="1" fill="currentColor" />
      </g>
      
      {/* PARAMOUNT+ Text */}
      <text
        x="60"
        y="28"
        fill="currentColor"
        fontFamily="Arial, sans-serif"
        fontSize="18"
        fontWeight="700"
        letterSpacing="1"
      >
        PARAMOUNT<tspan fill="#0064FF" fontSize="24">+</tspan>
      </text>
      
      {/* Subtitle */}
      <text
        x="60"
        y="45"
        fill="currentColor"
        fontFamily="Arial, sans-serif"
        fontSize="10"
        fontWeight="500"
        opacity="0.7"
        letterSpacing="2"
      >
        OPERATIONS HUB
      </text>
    </svg>
  );
};


