from pathlib import Path
from hashlib import sha256
from datetime import datetime as dt
from flask import render_template, redirect, url_for, send_file, flash

from webapp import app
from webapp.forms import StoryURLForm
from fte import fte


def _cleanup_tmp_dirs():
    root = Path(".")
    for tmp_dir in root.iterdir():
        conditions = [tmp_dir.is_dir()]
        conditions.append("tmpdir" in tmp_dir.name)
        conditions.append((tmp_dir / "tmp_ready").is_file())
        conditions.append(not (tmp_dir / "tmp_destroying").is_file())
        if all(conditions):
            tmp_dir.touch("tmp_destroying")
            for tmp_file in tmp_dir.iterdir():
                if tmp_file.is_file():
                    tmp_file.unlink(missing_ok=True)
            tmp_dir.rmdir()


@app.route("/", methods=["GET", "POST"])
def index():
    form = StoryURLForm()

    if form.validate_on_submit():
        _cleanup_tmp_dirs()

        tmp = f"tmpdir_{sha256(str(dt.now()).encode('utf-8')).hexdigest()}"
        tmp_dir = Path(tmp)
        tmp_dir.mkdir()

        try:
            if form.options.data == "download":
                fte(form.url.data, verbosity=True, dst_dir=tmp_dir.name)
                for item in tmp_dir.iterdir():
                    if item.is_file() and "tmp" not in item.name:
                        return send_file(item.resolve(), as_attachment=True)

            elif form.options.data == "upload":
                fte(form.url.data, verbosity=True, dst_dir=".")

        except Exception as e:
            flash(str(e))

        finally:
            (tmp_dir / "tmp_ready").touch()

        return redirect(url_for("index"))

    form.options.data = "download"
    return render_template(
        "index.html", title="Fanfiction-to-Ebook", form=form
    )
