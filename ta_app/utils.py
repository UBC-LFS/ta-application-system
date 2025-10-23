from datetime import datetime, date


# Role
SUPERADMIN = 'Superadmin'
ADMIN = 'Admin'
HR = 'HR'
INSTRUCTOR = 'Instructor'
STUDENT = 'Student'
OBSERVER = 'Observer'


# Application Status
NONE = '0'
SELECTED = '1'
OFFERED = '2'
ACCEPTED = '3'
DECLINED = '4'
CANCELLED = '5'

APP_STATUS = {
    'none': NONE,
    'applied': NONE,
    'selected': SELECTED,
    'offered': OFFERED,
    'accepted': ACCEPTED,
    'declined': DECLINED,
    'cancelled': CANCELLED
}


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