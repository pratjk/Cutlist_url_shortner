# Cutlist - Your Local URL Shortener

I built this because I wanted a simple, fast way to shorten URLs right on my own machine without relying on external services. Sometimes I just need a quick link for a local presentation or to share something temporarily on my home network, and I don't want to use bit.ly. Plus, it was a great way to learn how to build something full-stack!

## Features
- **Web Interface:** A simple, clean web page to paste long URLs and get short codes.
- **Custom Codes:** You can choose your own short code or let the app generate a random one.
- **QR Codes:** Every short link automatically gets a QR code so you can quickly open it on your phone!
- **Analytics & Tracking:** It tracks how many times a link was clicked, when it was last accessed, and even grabs the geographic location and referrer of the clickers (though location mapping only works on public IPs, local network clicks will just show up as "Local Network").
- **Management Dashboard:** You can view all your created links and delete them right from the browser.
- **CLI Mode:** Because terminal tools are cool, you can also manage everything right from the command line.

## Setup

First, make sure you have Python installed. Then, create a virtual environment and install the dependencies:

```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## Running the Web App

Just run the main file:

```bash
python app.py
```

Then open your browser and go to `http://localhost:5000`. The database (`cutlist.db`) will be automatically created the first time you run it.

## Running the CLI

If you want to manage your links from the terminal instead of the browser, run:

```bash
python app.py cli
```

This will launch a small menu where you can list links, view stats, delete links, or export everything to a CSV file.


## Learning is imp
It became apparent that ORM is not required when interacting with databases, and it is much better to simply write queries using `sqlite3`. Moreover, I learned how to work with QR codes using the `qrcode` package and perform basic web scraping to get geographic coordinates based on IP addresses. Despite the fact that the web app was not developed using any frameworks at all, it successfully does its thing.
