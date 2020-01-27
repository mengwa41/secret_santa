from service import app

if __name__ == '__main__':
    app.run(debug=True)

# from service import app, db
# from service.models import User, Group, Preference
#
# @app.shell_context_processor
# def make_shell_context():
#     return {'db': db, 'User': User, 'Group': Group, 'Preference': Preference}