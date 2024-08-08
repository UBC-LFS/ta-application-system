from datetime import datetime, date

TODAY = date.today()
THIS_YEAR = datetime.now().year
THIS_MONTH = datetime.now().month
THIS_DAY = datetime.now().day

NATIONALITY = {
    'domestic': '0',
    'international': '1'
}

LFS_FACULTY = 'faculty-of-land-and-food-systems'

UNDERGRADUATE = 'undergraduate-student'
MASTER = 'master-student'
PHD = 'phd-student'

TABLE_PAGE_SIZE = 20