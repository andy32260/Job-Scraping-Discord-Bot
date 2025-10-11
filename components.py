import aiohttp
import asyncio
from typing import List, Dict
import discord

white = 0xffffff
red = 0xff0000
green = 0x00ff00


class RapidAPIJobScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://jsearch.p.rapidapi.com"

    async def search_jobs(self, query: str, location: str = "", limit: int = 10,
                          remote_only: bool = False, min_salary: int = None,
                          date_posted: str = "all") -> List[Dict]:
        if not self.api_key:
            raise Exception("API key not configured")

        headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
        }

        search_query = query
        if location and not remote_only:
            search_query = f"{query} {location}"
        elif remote_only:
            search_query = f"{query} remote"

        params = {
            'query': search_query.strip(),
            'page': '1',
            'num_pages': '1',
            'date_posted': date_posted
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.base_url}/search",
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status == 429:
                        raise Exception("Rate limit exceeded. Please try again later.")
                    elif response.status == 401:
                        raise Exception("Invalid API key.")
                    elif response.status != 200:
                        raise Exception(f"API Error: {response.status}")

                    data = await response.json()
                    jobs = data.get('data', [])

                    filtered_jobs = self._filter_jobs(jobs, min_salary, remote_only)

                    unique_jobs = self._remove_duplicates(filtered_jobs)


                    return unique_jobs[:limit]

        except asyncio.TimeoutError:
            raise Exception("Search timed out. Please try again.")
        except Exception as e:
            raise e

    def _filter_jobs(self, jobs: List[Dict], min_salary: int = None,
                     remote_only: bool = False) -> List[Dict]:
        filtered = []
        for job in jobs:
            if not self._is_valid_job(job):
                continue

            if min_salary and job.get('job_min_salary'):
                if job.get('job_min_salary', 0) < min_salary:
                    continue

            if remote_only:
                job_title = job.get('job_title', '').lower()
                job_desc = job.get('job_description', '').lower()
                if not ('remote' in job_title or 'remote' in job_desc):
                    continue

            filtered.append(job)
        return filtered

    @staticmethod
    def _is_valid_job(job: Dict) -> bool:
        required_fields = ['job_title', 'employer_name']
        return all(job.get(field) for field in required_fields)

    @staticmethod
    def _remove_duplicates(jobs: List[Dict]) -> List[Dict]:
        seen = set()
        unique_jobs = []

        for job in jobs:
            key = (job.get('job_title', '').lower(),
                   job.get('employer_name', '').lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs


class JobNavigationView(discord.ui.View):
    def __init__(self, jobs: List[Dict], current_index: int = 0, user_id: int = None, db=None):
        super().__init__(timeout=300)
        self.jobs = jobs
        self.current_index = current_index
        self.user_id = user_id
        self.showing_full = False
        self.db = db

    def get_current_job(self) -> Dict:
        return self.jobs[self.current_index] if self.jobs else {}

    def create_embed(self, show_full: bool = False) -> discord.Embed:
        job = self.get_current_job()
        if not job:
            return discord.Embed(title="No job data", colour=red)

        description = job.get('job_description', 'No description')
        if not show_full:
            words = description.split()
            if len(words) > 150:
                description = ' '.join(words[:150]) + "...\n\n*Click 'Show Full Description' for more details*"

        embed = discord.Embed(
            title=job.get('job_title', 'N/A'),
            description=description[:4000],
            colour=white,
            url=job.get('job_apply_link', '')
        )

        embed.add_field(name="Company", value=job.get('employer_name', 'N/A'), inline=True)
        embed.add_field(name="Location", value=job.get('job_city', 'Remote'), inline=True)
        embed.add_field(name="Type", value=job.get('job_employment_type', 'N/A'), inline=True)

        if job.get('job_min_salary'):
            salary = f"${job.get('job_min_salary'):,}"
            if job.get('job_max_salary'):
                salary += f" - ${job.get('job_max_salary'):,}"
            embed.add_field(name="Salary", value=salary, inline=True)

        if job.get('job_posted_at_datetime_utc'):
            posted_date = job.get('job_posted_at_datetime_utc')
            if 'T' in posted_date:
                posted_date = posted_date.split('T')[0]
            embed.add_field(name="Posted", value=posted_date, inline=True)

        embed.set_footer(text=f"Job {self.current_index + 1} of {len(self.jobs)}")
        return embed

    @discord.ui.button(label='⟵', style=discord.ButtonStyle.secondary)
    async def previous_job(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.jobs) - 1
        embed = self.create_embed(self.showing_full)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='⟶', style=discord.ButtonStyle.secondary)
    async def next_job(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if self.current_index < len(self.jobs) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        embed = self.create_embed(self.showing_full)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Show Full Description', style=discord.ButtonStyle.primary)
    async def toggle_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.showing_full = not self.showing_full
        button.label = 'Show Less' if self.showing_full else 'Show Full Description'

        embed = self.create_embed(self.showing_full)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Save Job', style=discord.ButtonStyle.secondary)
    async def save_job(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if not self.user_id or not self.db:
            await interaction.response.send_message("Unable to identify user.", ephemeral=True)
            return

        job = self.get_current_job()
        if not job:
            await interaction.response.send_message("No job to save.", ephemeral=True)
            return

        success = self.db.add_bookmark(self.user_id, job)

        if success:
            await interaction.response.send_message(
                f"Saved '{job.get('job_title')}' at {job.get('employer_name')}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("Job has already been saved", ephemeral=True)

    @discord.ui.button(label='Apply Now', style=discord.ButtonStyle.success)
    async def apply_now(self, interaction: discord.Interaction, _button: discord.ui.Button):
        job = self.get_current_job()
        apply_link = job.get('job_apply_link') if job else None

        if apply_link:
            embed = discord.Embed(
                title="Apply below",
                description=f"**[Click here to apply for this position]({apply_link})**",
                colour=white
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("No application link available.")

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True



