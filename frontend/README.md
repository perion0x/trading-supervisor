# Trading Supervisor Frontend

A Next.js frontend for the Multi-Agent Trading Supervisor.

## Deploy to Vercel

1. Push this `frontend` folder to a GitHub repository
2. Go to [Vercel](https://vercel.com)
3. Click "New Project"
4. Import your GitHub repository
5. Set the root directory to `frontend`
6. Click "Deploy"

## Local Development

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## API Endpoint

The app connects to: `https://j0hz2ok0kb.execute-api.us-east-1.amazonaws.com/dev/analyze`

To update the API endpoint, edit `pages/index.js` and change the `API_URL` constant.
