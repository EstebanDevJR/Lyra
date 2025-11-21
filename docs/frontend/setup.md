# 🎨 Setup Guide - Lyra Frontend (Chatbot)

This guide will help you set up and configure the Lyra frontend application.

## Prerequisites

- Node.js 18.x or higher
- npm, yarn, or pnpm package manager
- Backend API running (see `Backend/SETUP.md`)

## Step 1: Install Dependencies

Navigate to the `Chatbot` directory and install dependencies:

```bash
cd Chatbot

# Using npm
npm install

# Using yarn
yarn install

# Using pnpm (recommended)
pnpm install
```

## Step 2: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env.local
```

2. Edit `.env.local` with your backend URL:

```env
# Backend API URL
# Change this if your backend is running on a different host/port
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Note:** If your backend is running on a different port or host, update this URL accordingly.

## Step 3: Verify Backend Connection

Make sure your backend is running before starting the frontend:

```bash
# In Backend directory
python src/main.py --port 8000
```

Test the connection:
```bash
curl http://localhost:8000/health
```

## Step 4: Run the Development Server

Start the Next.js development server:

```bash
# Using npm
npm run dev

# Using yarn
yarn dev

# Using pnpm
pnpm dev
```

The frontend will be available at:
- **Frontend**: http://localhost:3000
- **API Routes**: http://localhost:3000/api

## Step 5: Test the Application

1. Open http://localhost:3000 in your browser
2. Navigate to the chat interface
3. Try sending a test query
4. Verify that responses are received from the backend

## Troubleshooting

### Issue: "Failed to fetch" or CORS errors
- Verify backend is running on the correct port
- Check `NEXT_PUBLIC_API_URL` in `.env.local` matches backend URL
- Ensure backend `ALLOWED_ORIGINS` includes `http://localhost:3000`
- Restart both frontend and backend after changing CORS settings

### Issue: "Module not found" errors
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear Next.js cache: `rm -rf .next`
- Try using a different package manager

### Issue: Build errors
- Check Node.js version: `node --version` (should be 18+)
- Update dependencies: `npm update`
- Check for TypeScript errors: `npm run lint`

### Issue: API requests timing out
- Verify backend is running and accessible
- Check network connectivity
- Increase timeout in `lib/api.ts` if needed

### Issue: Environment variables not loading
- Make sure file is named `.env.local` (not `.env`)
- Restart the development server after changing `.env.local`
- Variables must start with `NEXT_PUBLIC_` to be accessible in browser

## Production Build

To create a production build:

```bash
# Build the application
npm run build

# Start production server
npm start
```

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` | Yes |

## Next Steps

1. **Customize the UI:**
   - Edit components in `components/` directory
   - Modify styles in `app/globals.css`
   - Update landing page content

2. **Add Features:**
   - Implement additional UI components
   - Add error handling improvements
   - Enhance user experience

3. **Deploy:**
   - Deploy to Vercel, Netlify, or your preferred platform
   - Update `NEXT_PUBLIC_API_URL` to production backend URL
   - Configure environment variables in your hosting platform

## Development Tips

- Use the browser DevTools to debug API calls
- Check the Network tab for request/response details
- Use React DevTools for component debugging
- Check backend logs for server-side issues

