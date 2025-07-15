import React from 'react'

export const SEAgentFactoryLogo: React.FC<{ className?: string }> = ({ className = "w-8 h-8" }) => (
  <svg 
    viewBox="0 0 100 100" 
    className={className}
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* Main angular shape */}
    <path 
      d="M35 10 L80 10 L80 30 L85 30 L85 55 L80 55 L80 85 L35 85 L10 60 L10 35 L35 10 Z" 
      fill="url(#mainGradient)" 
    />
    
    {/* Secondary rounded rectangle */}
    <rect 
      x="68" 
      y="52" 
      width="22" 
      height="28" 
      rx="7" 
      ry="7" 
      fill="url(#secondaryGradient)" 
    />
    
    <defs>
      <linearGradient id="mainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#E879F9" />
        <stop offset="50%" stopColor="#A855F7" />
        <stop offset="100%" stopColor="#3B82F6" />
      </linearGradient>
      <linearGradient id="secondaryGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#6366F1" />
        <stop offset="100%" stopColor="#4F46E5" />
      </linearGradient>
    </defs>
  </svg>
)
