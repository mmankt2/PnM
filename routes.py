from config import app
from controller_functions import index,edit,registration_page,register,login,logout,update_user,delete,blog
from controller_functions import schedulesession,schedulesessregistration,registerpt,loginpt,createevent
from controller_functions import delete_session,reschedule_template,reschedule_session
app.add_url_rule("/", view_func=index)
app.add_url_rule("/myaccount",view_func=edit)
app.add_url_rule('/login-register',view_func=registration_page)
app.add_url_rule("/logout",view_func=logout)
app.add_url_rule('/login',view_func=login)
app.add_url_rule('/users/<id>/update',view_func=update_user,methods=['POST'])
app.add_url_rule('users/<id>/destroy',view_func=delete)
app.add_url_rule('/blog',view_func=blog)
app.add_url_rule('/personaltraining/calendar',view_func=schedulesession)
app.add_url_rule('/personaltraining/schedulesession/login-register',view_func=schedulesessregistration)
app.add_url_rule('/register-schedulesession',view_func=registerpt,methods=['POST'])
app.add_url_rule('/login-schedulesession',view_func=registerpt,methods=['POST'])
app.add_url_rule('/createevent',view_func=createevent,methods=['POST'])
app.add_url_rule('/delete_session/<id>',view_func=delete_session,methods=['POST'])
app.add_url_rule('/reschedule_session/<id>',view_func=reschedule_template)
app.add_url_rule('/reschedule_session/<id>/update',view_func=reschedule_session,methods=['POST'])