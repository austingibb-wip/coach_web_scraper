# run scraping engine
# take list of labelled rows
# write to CSV

from scrapers.life_coach_school import LifeCoachSchoolScraper

def main():
    coaches = []
    lcs = LifeCoachSchoolScraper(coaches=coaches)
    lcs.load_all_coaches()

if __name__ == '__main__':
    main()
