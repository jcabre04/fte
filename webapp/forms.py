from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import DataRequired


class StoryURLForm(FlaskForm):
    url = StringField(
        "Story URL", validators=[DataRequired("Please enter a URL")]
    )
    options = RadioField(
        "Processing Options",
        choices=[("download", "Download"), ("upload", "Upload")],
        validators=[DataRequired("Please choose an option")],
    )
    submit = SubmitField("Submit")
