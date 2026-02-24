import { motion } from 'motion/react';

export function DeepRedLogo({ size = 40 }: { size?: number }) {
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      whileHover={{ scale: 1.1, rotate: 5 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      {/* Outer glow circle */}
      <motion.circle
        cx="50"
        cy="50"
        r="45"
        fill="url(#redGradient)"
        opacity="0.2"
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      {/* Main circle */}
      <circle
        cx="50"
        cy="50"
        r="40"
        fill="url(#redGradient)"
      />
      
      {/* Letter D - left arc */}
      <path
        d="M 35 30 L 40 30 L 40 70 L 35 70 Z M 40 30 Q 60 30 60 50 Q 60 70 40 70"
        fill="white"
        stroke="white"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      
      {/* Letter R - right side with angle */}
      <path
        d="M 65 30 L 70 30 L 70 70 L 65 70 Z M 65 30 L 75 30 Q 82 30 82 40 Q 82 47 75 47 L 65 47 M 75 47 L 82 70 L 77 70 L 70 47"
        fill="white"
        stroke="white"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      
      {/* Center dot accent */}
      <motion.circle
        cx="50"
        cy="50"
        r="3"
        fill="#DC143C"
        animate={{
          scale: [1, 1.5, 1],
          opacity: [1, 0.5, 1],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
        }}
      />
      
      {/* Gradients */}
      <defs>
        <linearGradient id="redGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#DC143C" />
          <stop offset="50%" stopColor="#EF4444" />
          <stop offset="100%" stopColor="#EC4899" />
        </linearGradient>
      </defs>
    </motion.svg>
  );
}
