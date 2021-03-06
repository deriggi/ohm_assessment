from flask import jsonify, render_template, request, Response
from flask.ext.login import current_user, login_user

from functions import app
from models import User


@app.route('/community', methods=['GET'])
def community():

    login_user(User.query.get(1))
    most_recent = User.get_most_recent()
    
    args = {
            'gift_card_eligible': True,
            'cashout_ok': True,
            'user_below_silver': current_user.is_below_tier('Silver'),
            'most_recent':most_recent
    }
    return render_template("community.html", **args)

@app.route('/download', methods=['GET'])
def getPlotCSV():
   try:    
      id = request.args.get("id")
      csv = User.get_as_csv(id)
   except:
      csv="no_data\n"
   return Response(
      csv,
      mimetype="text/csv",
      headers={"Content-disposition":
                 "attachment; filename=userrow.csv"})