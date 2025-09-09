from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required, admin_only
from incontext.db import get_db
from incontext.db import dict_factory


bp = Blueprint('master_lists', __name__, url_prefix='/master-lists')


@bp.route('/')
@login_required
@admin_only
def index():
    master_lists = get_master_lists()
    return render_template('master-lists/index.html', master_lists=master_lists)


@bp.route('/new', methods=('GET', 'POST'))
@login_required
@admin_only
def new():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO master_lists (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            db.commit()
            return redirect(url_for('master_lists.index'))
    return render_template('master-lists/new.html')


@bp.route('/<int:master_list_id>/view')
@login_required
def view(master_list_id):
    master_list = get_master_list(master_list_id, False)
    return render_template('master-lists/view.html', master_list=master_list)


@bp.route('/<int:master_list_id>/edit', methods=('GET', 'POST'))
@login_required
@admin_only
def edit(master_list_id):
    master_list = get_master_list(master_list_id)
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
                error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE master_lists SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, master_list_id)
            )
            db.commit()
            return redirect(url_for('master_lists.index'))
    return render_template("master-lists/edit.html", master_list=master_list)


@bp.route("<int:master_list_id>/delete", methods=("POST",))
@login_required
@admin_only
def delete(master_list_id):
    master_list = get_master_list(master_list_id)
    db = get_db()
    # Delete master-related details
    db.execute(
        'DELETE FROM master_details'
        ' WHERE id IN'
        ' (SELECT master_detail_id FROM master_list_detail_relations WHERE master_list_id = ?)',
        (master_list_id,)
    )
    # Delete master-related items
    db.execute(
        'DELETE FROM master_items'
        ' WHERE id IN'
        ' (SELECT master_item_id FROM master_list_item_relations WHERE master_list_id = ?)',
        (master_list_id,)
    )
    # Delete item-detail relations
    db.execute(
        'DELETE FROM master_item_detail_relations'
        ' WHERE master_item_id IN'
        ' (SELECT master_item_id FROM master_list_item_relations WHERE master_list_id = ?)',
        (master_list_id,)
    )
    # Delete master-item relations
    db.execute('DELETE FROM master_list_item_relations WHERE master_list_id = ?',(master_list_id,))
    # Delete master-detail relations
    db.execute('DELETE FROM master_list_detail_relations WHERE master_list_id = ?', (master_list_id,))
    # Delete master
    db.execute('DELETE FROM master_lists WHERE id = ?', (master_list_id,))
    db.commit()
    return redirect(url_for('master_lists.index'))


@bp.route('<int:master_list_id>/master-items/new', methods=("GET", "POST"))
@login_required
@admin_only
def new_master_item(master_list_id):
    master_list = get_master_list(master_list_id)
    if request.method == "POST":
        name = request.form['name']
        master_detail_contents = []
        master_details = [master_detail for master_detail in master_list['master_details']]
        for master_detail in master_details:
            master_detail_id = master_detail['id']
            master_content = request.form[str(master_detail_id)]
            master_detail_contents.append((master_detail_id, master_content))
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO master_items (name, creator_id)'
                ' VALUES (?, ?)',
                (name, g.user['id'])
            )
            master_item_id = cur.lastrowid
            cur.execute(
                'INSERT INTO master_list_item_relations (master_list_id, master_item_id)'
                ' VALUES (?, ?)',
                (master_list_id, master_item_id)
            )
            master_i_d_relations = []
            for master_detail_content in master_detail_contents:
                master_i_d_relations.append((master_item_id,) + master_detail_content)
            cur.executemany(
                'INSERT INTO master_item_detail_relations (master_item_id, master_detail_id, master_content)'
                ' VALUES(?, ?, ?)',
                master_i_d_relations
            )
            db.commit()
            return redirect(url_for('master_lists.view', master_list_id=master_list_id))
    return render_template("master-lists/master-items/new.html", master_list=master_list)


@bp.route("<int:master_list_id>/master-items/<int:master_item_id>/view")
@login_required
def view_master_item(master_list_id, master_item_id):
    master_list = get_master_list(master_list_id, False)
    requested_master_item = None
    for master_item in master_list['master_items']:
        if master_item['id'] == master_item_id:
            requested_master_item = master_item
    if not requested_master_item:
        abort(404)
    return render_template("master-lists/master-items/view.html", master_list=master_list, master_item=requested_master_item, master_details=master_list["master_details"])


@bp.route("<int:master_list_id>/master-items/<int:master_item_id>/edit", methods=("GET", "POST"))
@login_required
@admin_only
def edit_master_item(master_list_id, master_item_id):
    master_list = get_master_list(master_list_id)
    requested_master_item = next((master_item for master_item in master_list["master_items"] if master_item["id"] == master_item_id), None)
    if not requested_master_item:
        abort(404)
    if request.method == "POST":
        name = request.form['name']
        master_i_d_relations = []
        master_details = [master_detail for master_detail in master_list['master_details']]
        for master_detail in master_details:
            master_detail_id = master_detail['id']
            master_detail_content = request.form[str(master_detail_id)]
            master_i_d_relations.append((master_detail_content, master_item_id, master_detail_id))
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE master_items SET name = ?'
                ' WHERE id = ?',
                (name, master_item_id)
            )
            db.executemany(
                'UPDATE master_item_detail_relations'
                ' SET master_content = ?'
                ' WHERE master_item_id = ?'
                ' AND master_detail_id = ?',
                master_i_d_relations
            )
            db.commit()
            return redirect(url_for('master_lists.view', master_list_id=master_list_id))
    return render_template("master-lists/master-items/edit.html", master_list=master_list, master_item=requested_master_item)


@bp.route("<int:master_list_id>/master-items/<int:master_item_id>/delete", methods=("POST",))
@login_required
@admin_only
def delete_master_item(master_list_id, master_item_id):
    master_list = get_master_list(master_list_id)
    requested_master_item = next((master_item for master_item in master_list["master_items"] if master_item["id"] == master_item_id), None)
    if not requested_master_item:
        abort(404)
    master_details = master_list["master_details"]
    db = get_db()
    db.execute('DELETE FROM master_items WHERE id = ?', (master_item_id,))
    db.execute('DELETE FROM master_item_detail_relations WHERE master_item_id = ?', (master_item_id,))
    db.execute(
        'DELETE from master_list_item_relations'
        ' WHERE master_list_id = ? AND master_item_id = ?',
        (master_list_id, master_item_id)
    )
    db.commit()
    return redirect(url_for('master_lists.view', master_list_id=master_list_id))


@bp.route("/<int:master_list_id>/master-details/new", methods=("GET", "POST"))
@login_required
@admin_only
def new_master_detail(master_list_id):
    master_list = get_master_list(master_list_id)
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO master_details (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            master_detail_id = cur.lastrowid
            cur.execute(
                'INSERT INTO master_list_detail_relations (master_list_id, master_detail_id)'
                ' VALUES (?, ?)',
                (master_list_id, master_detail_id)
            )
            master_items = master_list["master_items"]
            data = [(master_item['id'], master_detail_id, '') for master_item in master_items]
            cur.executemany(
                'INSERT INTO master_item_detail_relations (master_item_id, master_detail_id, master_content)'
                'VALUES (?, ?, ?)',
                data
            )
            tethered_lists = cur.execute(
                "SELECT lir.item_id, lir.list_id"
                " FROM list_item_relations lir"
                " RIGHT JOIN list_tethers lt"
                " ON lt.list_id = lir.list_id"
                " WHERE lt.master_list_id = ?",
                (master_list_id,)
            ).fetchall()
            entries = []
            for tethered_list in tethered_lists:
                entries.append([
                    tethered_list["list_id"],
                    tethered_list["item_id"],
                    master_detail_id,
                    ""
                ])
            if entries:
                cur.executemany(
                    "INSERT INTO untethered_content (list_id, item_id, master_detail_id, content)"
                    " VALUES (?, ?, ?, ?)",
                    entries
                )
            db.commit()
            return redirect(url_for('master_lists.view', master_list_id=master_list["id"]))
    return render_template("master-lists/master-details/new.html", master_list=master_list)


@bp.route("/<int:master_list_id>/master-details/<int:master_detail_id>/edit", methods=("GET", "POST"))
@login_required
@admin_only
def edit_master_detail(master_list_id, master_detail_id):
    master_list = get_master_list(master_list_id)
    requested_master_detail = next((master_detail for master_detail in master_list["master_details"] if master_detail["id"] == master_detail_id), None)
    if requested_master_detail is None:
        abort(404)
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE master_details SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, master_detail_id)
            )
            db.commit()
            return redirect(url_for('master_lists.view', master_list_id=master_list_id))
    return render_template("master-lists/master-details/edit.html", master_list=master_list, master_detail=requested_master_detail)


@bp.route('/<int:master_list_id>/master-details/<int:master_detail_id>/delete', methods=('POST',))
@login_required
@admin_only
def delete_master_detail(master_list_id, master_detail_id):
    master_list = get_master_list(master_list_id)
    requested_master_detail = next((master_detail for master_detail in master_list["master_details"] if master_detail["id"] == master_detail_id), None)
    if not requested_master_detail:
        abort(404)
    db = get_db()
    db.execute('DELETE FROM master_details WHERE id = ?', (master_detail_id,))
    db.execute('DELETE FROM master_item_detail_relations WHERE master_detail_id = ?', (master_detail_id,))
    db.execute('DELETE FROM master_list_detail_relations WHERE master_detail_id = ?', (master_detail_id,))
    db.commit()
    return redirect(url_for('master_lists.view', master_list_id=master_list_id))


def get_master_lists():
    db = get_db()
    master_lists = db.execute(
        "SELECT m.id, m.name, m.description, m.created, u.username"
        " FROM master_lists m"
        " JOIN users u"
        " ON u.id = m.creator_id"
    ).fetchall()
    return master_lists


def get_master_list(master_list_id, check_access=True):
    db = get_db()
    db.row_factory = dict_factory
    master_list = db.execute(
        "SELECT m.id, m.creator_id, m.created, m.name, m.description, u.username"
        " FROM master_lists m"
        " JOIN users u"
        " ON u.id = m.creator_id"
        " WHERE m.id = ?",
        (master_list_id,)
    ).fetchone()
    if master_list is None:
        abort(404)
    if check_access:
        if not g.user["admin"]:
            abort(403)
    master_list_ext = {}
    for key in master_list.keys():
        master_list_ext[key] = master_list[key]
    master_items = db.execute(
        'SELECT i.id, i.name, i.created, u.username'
        ' FROM master_items i'
        ' JOIN master_list_item_relations m'
        ' ON m.master_item_id = i.id'
        ' JOIN users u'
        ' ON u.id = i.creator_id'
        ' WHERE m.master_list_id = ?',
        (master_list_id,)
    ).fetchall()
    master_list_ext['master_items'] = []
    for master_item in master_items:
        new_master_item = {}
        for key in master_item.keys():
            new_master_item[key] = master_item[key]
        new_master_item['master_contents'] = []
        master_item_id = str(master_item['id'])
        master_list_ext['master_items'].append(new_master_item)
    master_details = db.execute(
        'SELECT d.id, d.name, d.description'
        ' FROM master_details d'
        ' JOIN master_list_detail_relations m'
        ' ON m.master_detail_id = d.id'
        ' WHERE m.master_list_id = ?',
        (master_list_id,)
    ).fetchall()
    master_list_ext['master_details'] = master_details
    master_contents = db.execute(
        'SELECT master_item_id, master_content'
        ' FROM master_item_detail_relations'
        ' WHERE master_detail_id IN'
        ' (SELECT master_detail_id'
        '  FROM master_list_detail_relations'
        '  WHERE master_list_id = ?)',
        (master_list_id,)
    ).fetchall()
    for master_content in master_contents:
        master_item_id = master_content['master_item_id']
        master_item = next((master_item for master_item in master_list_ext["master_items"] if master_item["id"] == master_item_id), None)
        master_item['master_contents'].append(master_content['master_content'])
    return master_list_ext
