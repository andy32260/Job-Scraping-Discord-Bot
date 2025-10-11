import discord
from datetime import datetime
from components import JobNavigationView



def parse_job_command(args: str) -> tuple:
    location = ""
    limit = 10
    remote_only = False
    min_salary = None
    date_posted = "all"

    parts = args.split()
    i = 0
    query_parts = []

    while i < len(parts):
        part = parts[i].lower()

        if part == "--location" and i + 1 < len(parts):
            location = parts[i + 1]
            i += 2
        elif part == "--limit" and i + 1 < len(parts):
            try:
                limit = max(1, min(20, int(parts[i + 1])))
            except ValueError:
                pass
            i += 2
        elif part == "--salary" and i + 1 < len(parts):
            try:
                min_salary = int(parts[i + 1])
            except ValueError:
                pass
            i += 2
        elif part == "--remote":
            remote_only = True
            i += 1
        elif part == "--recent":
            date_posted = "today"
            i += 1
        elif part == "--week":
            date_posted = "3days"
            i += 1
        else:
            query_parts.append(parts[i])
            i += 1

    query = " ".join(query_parts)
    return query, location, limit, remote_only, min_salary, date_posted

def setup_commands(bot, db, job_scraper, recent_jobs, colors):
    red, white, green = colors

    @bot.command(name='jobs')
    async def search_jobs(ctx, *, search_query: str = ""):
        if not search_query.strip():
            embed = discord.Embed(
                title="Invalid Search",
                description="Please provide a search query\n\n**Example:**\n`.jobs python developer --location london --limit 5 --salary 50000`",
                colour=red
            )
            await ctx.send(embed=embed)
            return

        query, location, limit, remote_only, min_salary, date_posted = parse_job_command(search_query)

        if not query.strip():
            embed = discord.Embed(
                title="Invalid Search",
                description="Please provide a job title or keywords",
                colour=red
            )
            await ctx.send(embed=embed)
            return

        user_id = ctx.author.id

        db.add_search_history(user_id, search_query)

        embed = discord.Embed(
            title="Searching for Jobs...",
            description=f"**Query:** {query}\n**Location:** {location or 'Any'}\n**Limit:** {limit}",
            colour=white
        )
        message = await ctx.send(embed=embed)

        try:
            jobs = await job_scraper.search_jobs(
                query, location, limit, remote_only, min_salary, date_posted
            )

            recent_jobs.extend(jobs[:5])
            recent_jobs[:] = recent_jobs[-20:]

            if not jobs:
                embed = discord.Embed(
                    title="No Jobs Found",
                    description="Try different keywords or remove some filters",
                    colour=red
                )
                await message.edit(embed=embed)
                return

            view = JobNavigationView(jobs, 0, user_id, db)
            embed = view.create_embed()
            await message.edit(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(
                title="Search Error",
                description=f"**Error:** {str(e)}\n\nPlease try again later or contact an admin.",
                colour=red
            )
            await message.edit(embed=embed)


    @bot.command(name='jobsloc')
    async def search_jobs_location(ctx, location: str, *, job_query: str):
        full_query = f"{job_query} --location {location}"
        await search_jobs(ctx, search_query=full_query)


    @bot.command(name='recent')
    async def recent_jobs_command(ctx, limit: int = 5):
        if not recent_jobs:
            embed = discord.Embed(
                title="No Recent Jobs",
                description="No jobs have been searched recently. Try using `.jobs` first",
                colour=white
            )
            await ctx.send(embed=embed)
            return

        limit = max(1, min(10, limit))
        jobs_to_show = recent_jobs[-limit:]

        view = JobNavigationView(jobs_to_show, 0, ctx.author.id, db)
        embed = view.create_embed()
        embed.title = f"{embed.title}"
        await ctx.send(embed=embed, view=view)


    @bot.command(name='saved')
    async def show_saved_jobs(ctx):
        user_id = ctx.author.id

        saved_jobs = db.get_bookmarks(user_id)

        if not saved_jobs:
            embed = discord.Embed(
                title="No Saved Jobs",
                description="You haven't saved any jobs yet. Use the 'Save' button when viewing jobs",
                colour=white
            )
            await ctx.send(embed=embed)
            return

        view = JobNavigationView(saved_jobs, 0, user_id, db)
        embed = view.create_embed()
        embed.title = f"{embed.title}"
        await ctx.send(embed=embed, view=view)


    @bot.command(name='history')
    async def search_history(ctx):
        user_id = ctx.author.id

        history = db.get_search_history(user_id)

        if not history:
            embed = discord.Embed(
                title="No Search History",
                description="You haven't searched for jobs yet",
                colour=white
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Your Search History",
            colour=white
        )

        for i, search in enumerate(history, 1):
            try:
                timestamp = datetime.fromisoformat(search['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime("%m/%d %H:%M")
            except:
                time_str = search['timestamp'][:16]

            embed.add_field(
                name=f"{i}. {time_str}",
                value=f"`{search['query']}`",
                inline=False
            )

        await ctx.send(embed=embed)


    @bot.command(name='health')
    async def bot_health(ctx):
        embed = discord.Embed(title="Health Check", colour=green)

        try:
            _ = await job_scraper.search_jobs("test", limit=1)
            api_status = "Healthy"
            api_colour = green
        except Exception as e:
            api_status = f"Error: {str(e)[:100]}"
            api_colour = red

        embed.add_field(name="Bot Status", value="Online", inline=True)
        embed.add_field(name="API Status", value=api_status, inline=True)
        embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)

        embed.colour = api_colour
        await ctx.send(embed=embed)


    @bot.command(name='clear')
    async def clear_user_data(ctx, data_type: str = ""):
        user_id = ctx.author.id

        if data_type.lower() == "saved":
            count = db.clear_bookmarks(user_id)
            await ctx.send(f"Cleared {count} saved jobs")

        elif data_type.lower() == "history":
            count = db.clear_search_history(user_id)
            await ctx.send(f"Cleared {count} search history entries")

        elif data_type.lower() == "all":
            saved_count, history_count = db.clear_all_user_data(user_id)
            await ctx.send(f"Cleared all data: {saved_count} saved jobs, {history_count} history entries")

        else:
            embed = discord.Embed(
                title="Clear Data",
                description="**Usage:**\n`.clear saved` - Clear saved jobs\n`.clear history` - Clear search history\n`.clear all` - Clear everything",
                colour=white
            )
            await ctx.send(embed=embed)


    @bot.command(name='help')
    async def help_command(ctx):
        embed = discord.Embed(
            title="Job Bot Help",
            colour=white
        )

        embed.add_field(
            name="Basic Search Examples",
            value="`.jobs python developer`\n`.jobs marketing manager --location london`\n\u200b",
            inline=False
        )

        embed.add_field(
            name="Detailed Search Examples",
            value="`.jobs python --location remote --salary 70000 --limit 10`\n"
                  "`.jobs data scientist --remote --recent`\n\u200b",
            inline=False
        )

        embed.add_field(
            name="Searches based on Location",
            value="`.jobsloc london python developer`\n`.jobsloc \"new york\" software engineer`\n\u200b",
            inline=False
        )

        embed.add_field(
            name="Filters & Options",
            value="`--location [city]` - Specific location\n"
                  "`--salary [amount]` - Minimum salary\n"
                  "`--remote` - Remote jobs only\n"
                  "`--limit [1-20]` - Number of results\n"
                  "`--recent` - Jobs from today\n"
                  "`--week` - Jobs from this week\n\u200b",
            inline=False
        )

        embed.add_field(
            name="Navigation",
            value="`⟵ ⟶` - To browse jobs\n"
                  "`Show Full Description` - Shows full description\n"
                  "`Save job` - Saves a job\n"
                  "`Apply now` - Sends a link to the job posting\n\u200b",
            inline=False
        )

        embed.add_field(
            name="Viewing Saved jobs & Search history",
            value="`.saved` - View bookmarked jobs\n"
                  "`.history` - Your search history\n"
                  "`.recent` - Recently found jobs\n\u200b",
            inline=False
        )

        embed.add_field(
            name="Managing Saved jobs and Search history",
            value="`.clear saved` - Clear bookmarked jobs\n"
                  "`.clear history` - Clear search history\n"
                  "`.clear all` - Clear everything",
            inline=False
        )

        await ctx.send(embed=embed)
