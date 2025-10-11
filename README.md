# Job Search Discord Bot

A Discord bot that helps you search for jobs, bookmark opportunities, and track your search history without leaving Discord.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Demo

<img width="889" height="955" alt="Discord Bot Preview" src="https://github.com/user-attachments/assets/bb667b53-478c-4bae-9e27-85850f740bd3" />


## Features

- 🔍 Search jobs with filters (location, salary, remote work)
- 💾 Bookmark jobs you're interested in
- 📝 Track your search history
- 🎯 Interactive navigation with Discord buttons
- ⚡ Fast search powered by JSearch API

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/job-search-bot.git
cd job-search-bot

# Install dependencies
pip install discord.py aiohttp python-dotenv

# Set up your .env file
DISCORD_TOKEN=your_discord_token
RAPIDAPI_KEY=your_rapidapi_key

# Run the bot
python main.py
```

## Usage

**Search for jobs:**
```
.jobs python developer
.jobs data analyst --location london --salary 50000
.jobs software engineer --remote
```

**Manage bookmarks:**
```
.saved      # View saved jobs
.history    # View search history
.recent     # View recent results
```

**Available filters:**
- `--location` - Filter by city
- `--salary` - Minimum salary
- `--remote` - Remote only
- `--limit` - Number of results (1-20)
- `--recent` - Today's jobs
- `--week` - This week's jobs

## Tech Stack

- Python 3.8+
- Discord.py - Discord API wrapper
- aiohttp - Async HTTP requests
- SQLite - Data persistence
- JSearch API - Job listings

## Project Structure

```
├── main.py          # Bot initialization
├── commands.py      # Command handlers
├── components.py    # Job scraper and UI
├── database.py      # Database operations
└── .env            # Environment variables
```

## Why I Built This

I was tired of switching between multiple job sites while also keeping up with Discord communities. Wanted something that combined both, and learned about Discord bot development in the process.

## Challenges

- **Discord embed limits** - Had to truncate long job descriptions
- **API rate limits** - Added proper error handling for rate limit responses
- **Async programming** - First time working with Python's async/await patterns
- **State management** - Keeping track of which user is viewing which job

## What I Learned

- Working with Discord.py and building interactive UI components
- Integrating third-party REST APIs
- Database design with SQLite
- Async/await patterns in Python
- Error handling for network requests

## Roadmap

- [ ] Email notifications for saved searches
- [ ] Export bookmarks to CSV
- [ ] Track application status
- [ ] Support for more job boards
- [ ] Salary comparison charts

## Contributing

Pull requests are welcome! Feel free to open an issue if you find bugs or have feature suggestions.

## License

MIT

## Acknowledgments

- [Discord.py](https://github.com/Rapptz/discord.py) for the amazing library
- [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) for job data

---

**Made by [Your Name]** • [GitHub](https://github.com/yourusername) • [LinkedIn](https://linkedin.com/in/yourprofile)
