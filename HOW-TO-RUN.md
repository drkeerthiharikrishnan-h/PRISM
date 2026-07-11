# How to Run Facet on Your Computer

Hi Keerthi! Follow these steps and Facet will be running on your laptop in about 5 minutes.

---

## What You Need First

### Step 1 — Install Docker Desktop

Docker is a free tool that runs the app inside a safe container. You only install it once.

1. Go to: **https://www.docker.com/products/docker-desktop/**
2. Click **"Download for Mac"** (choose Apple Chip if you have an M1/M2/M3 Mac)
3. Open the downloaded file and drag Docker to your Applications folder
4. Open Docker from your Applications — you'll see a whale icon in your menu bar
5. Wait until the whale icon stops animating (means Docker is ready)

---

### Step 2 — Get the Project Files

Balaji will share the project folder with you. It should be called **Facet** and contain files like `main.py`, `docker-compose.yml`, etc.

Put the Facet folder somewhere easy to find — like your Desktop or Documents.

---

### Step 3 — Add the API Keys

Inside the Facet folder, find the file called **`.env`**

> Note: Files starting with `.` are hidden on Mac. If you can't see `.env`, open Terminal and type:
> ```
> open -a TextEdit /path/to/Facet/.env
> ```
> Or ask Balaji to set this up for you — it only needs to be done once.

The `.env` file needs two API keys — **Balaji will share these with you directly.**

Once you receive them, the file should look like:
```
ANTHROPIC_API_KEY=<key Balaji will send>
NCBI_API_KEY=<key Balaji will send>
```

---

## Running the App

### Step 4 — Open Terminal

On your Mac: press **Command + Space**, type **Terminal**, press Enter.

---

### Step 5 — Navigate to the Facet folder

In Terminal, type (replace the path with where your Facet folder is):

```bash
cd ~/Desktop/Facet
```

---

### Step 6 — Start the App

Type this one command and press Enter:

```bash
docker compose up
```

The first time you run this it will download some things — this takes about 2–3 minutes. You'll see a lot of text scrolling. That's normal!

When you see this line, the app is ready:

```
✅  Application startup complete.
```

---

### Step 7 — Open Facet in Your Browser

Open **Safari** or **Chrome** and go to:

```
http://localhost:8000
```

You should see the Facet login screen with the researcher profiles! 🎉

---

## Stopping the App

When you're done, go back to Terminal and press:

```
Control + C
```

This stops the app. To start it again, just do Step 6 again (it will be much faster the second time).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Cannot connect to Docker daemon" | Make sure Docker Desktop is open (whale in menu bar) |
| Page won't load | Wait 30 seconds after seeing "startup complete", then refresh |
| App shows errors | Check that `.env` has the correct API keys |
| Port 8000 is in use | Change `"8000:8000"` to `"8001:8000"` in docker-compose.yml, then visit localhost:8001 |

---

## Quick Reference

| Action | Command |
|---|---|
| Start app | `docker compose up` |
| Start app (in background) | `docker compose up -d` |
| Stop app | `Control + C` (or `docker compose down`) |
| Restart app | `docker compose restart` |
| See logs | `docker compose logs -f` |

---

*Built for the Gladstone Institute × Cerebral Valley Hackathon 2026*
