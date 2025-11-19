/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",  // 识别 src 下所有 Vue/JS 文件
  ],
  theme: {
    extend: {
      colors: {
        // 原HTML中的自定义颜色
        primary: '#2563eb',
        secondary: '#64748b',
        accent: '#f59e0b',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        light: '#f1f5f9',
        dark: '#1e293b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

