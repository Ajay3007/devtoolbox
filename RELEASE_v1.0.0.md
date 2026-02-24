# PCAP Editor v1.0.0 Release Notes

## Stable Release for Production Deployment

This v1.0.0 release prepares the PCAP Editor application for production hosting environments, specifically supporting a split deployment strategy (e.g., Render for Backend + Vercel for Frontend). 

### Key Changes
- **Environment Variable Support**: Replaced hardcoded localhost URLs `http://localhost:5000/api` with Vite-compatible environment variables (`VITE_API_BASE_URL`) in the Vue frontend.
- **Dynamic Port Binding**: Updated the Flask backend to respect the dynamic `PORT` injected by hosting providers like Render.
- **Production Safety Toggle**: Tied `FLASK_DEBUG` via `.env` parameter instead of hardcoding `debug=True` in `backend/app.py`.
- **Systematic Build Script Correction**: Replaced deprecated `vue-cli-service` scripts with Vite equivalent `vite build` to guarantee successful production bundles.
- **Documentation**: Added `.env.example` templates to both `frontend` and `backend` directories to guide first-time deployments.

### Deployment Instructions (Option 2: Render + Vercel)

If you plan to deploy using the split-hosting architecture:

#### Step 1: Deploy Backend to Render
1. Create a new **Web Service** on [Render.com](https://render.com/).
2. Connect your GitHub repository.
3. Configure the settings:
   - Root Directory: `backend`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Set Environment Variables:
   - `FLASK_DEBUG` = `False`
5. Deploy and copy your new backend URL (e.g., `https://pcap-editor-api.onrender.com`).

#### Step 2: Deploy Frontend to Vercel
1. Create a new **Project** on [Vercel.com](https://vercel.com/).
2. Connect your GitHub repository.
3. Configure the settings:
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
4. Set Environment Variables:
   - `VITE_API_BASE_URL` = `<YOUR_RENDER_BACKEND_URL>/api` (replace with the URL from Step 1)
5. Hit Deploy.

---

*Thank you for exploring PCAP editing solutions.*
