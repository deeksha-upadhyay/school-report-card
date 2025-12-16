from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from app import app, db
from io import BytesIO
from weasyprint import HTML
import os


def calculate_grade(percentage):
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "E"


@app.route("/student/new", methods=["GET", "POST"])
@login_required
def new_student():
    if request.method == "POST":
        school_name = request.form.get("school_name")
        student_name = request.form.get("student_name")
        class_name = request.form.get("class_name")
        division = request.form.get("division")
        roll_no = request.form.get("roll_no")
        academic_year = request.form.get("academic_year")
        address = request.form.get("address")
        teacher_remark = request.form.get("teacher_remark")
        principal_remark = request.form.get("principal_remark")
        subject_names = request.form.getlist("subject_name")
        max_marks_list = request.form.getlist("max_marks")
        obtained_list = request.form.getlist("obtained_marks")
        # e.g. "images/students/deeksha.jpg" (no leading 'static/')
        profile_photo = request.form.get("profile_photo")

        subjects = []
        total_max = 0
        total_obtained = 0

        for name, max_m, obt_m in zip(subject_names, max_marks_list, obtained_list):
            if not name:
                continue
            max_m = int(max_m) if max_m else 0
            obt_m = int(obt_m) if obt_m else 0
            total_max += max_m
            total_obtained += obt_m
            subjects.append({
                "name": name,
                "max_marks": max_m,
                "obtained_marks": obt_m
            })

        percentage = (total_obtained / total_max) * 100 if total_max > 0 else 0
        grade = calculate_grade(percentage)

        student_doc = {
            "professor_id": current_user.id,
            "school_name": school_name,
            "student_name": student_name,
            "class_name": class_name,
            "division": division,
            "roll_no": roll_no,
            "academic_year": academic_year,
            "address": address,
            "profile_photo": profile_photo,
            "teacher_remark": teacher_remark,
            "principal_remark": principal_remark,
            "subjects": subjects,
            "total_max": total_max,
            "total_obtained": total_obtained,
            "percentage": round(percentage, 2),
            "grade": grade
        }

        result = db.students.insert_one(student_doc)
        flash("Student report created", "success")
        return redirect(url_for("preview_report", student_id=str(result.inserted_id)))

    return render_template("student_form.html")


@app.route("/student/<student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    student = db.students.find_one(
        {"_id": ObjectId(student_id), "professor_id": current_user.id}
    )
    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        school_name = request.form.get("school_name")
        student_name = request.form.get("student_name")
        class_name = request.form.get("class_name")
        division = request.form.get("division")
        roll_no = request.form.get("roll_no")
        academic_year = request.form.get("academic_year")
        address = request.form.get("address")
        teacher_remark = request.form.get("teacher_remark")
        principal_remark = request.form.get("principal_remark")
        subject_names = request.form.getlist("subject_name")
        max_marks_list = request.form.getlist("max_marks")
        obtained_list = request.form.getlist("obtained_marks")
        profile_photo = request.form.get("profile_photo")

        subjects = []
        total_max = 0
        total_obtained = 0

        for name, max_m, obt_m in zip(subject_names, max_marks_list, obtained_list):
            if not name:
                continue
            max_m = int(max_m) if max_m else 0
            obt_m = int(obt_m) if obt_m else 0
            total_max += max_m
            total_obtained += obt_m
            subjects.append({
                "name": name,
                "max_marks": max_m,
                "obtained_marks": obt_m
            })

        percentage = (total_obtained / total_max) * 100 if total_max > 0 else 0
        grade = calculate_grade(percentage)

        db.students.update_one(
            {"_id": ObjectId(student_id), "professor_id": current_user.id},
            {"$set": {
                "school_name": school_name,
                "student_name": student_name,
                "class_name": class_name,
                "division": division,
                "roll_no": roll_no,
                "academic_year": academic_year,
                "address": address,
                "profile_photo": profile_photo,
                "teacher_remark": teacher_remark,
                "principal_remark": principal_remark,
                "subjects": subjects,
                "total_max": total_max,
                "total_obtained": total_obtained,
                "percentage": round(percentage, 2),
                "grade": grade
            }}
        )

        flash("Student report updated", "success")
        return redirect(url_for("preview_report", student_id=student_id))

    return render_template("student_form.html", student=student, mode="edit")


@app.route("/student/<student_id>/preview")
@login_required
def preview_report(student_id):
    student = db.students.find_one(
        {"_id": ObjectId(student_id), "professor_id": current_user.id}
    )
    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("dashboard"))
    return render_template("report_preview.html", student=student)


@app.route("/student/<student_id>/pdf")
@login_required
def student_pdf(student_id):
    student = db.students.find_one(
        {"_id": ObjectId(student_id), "professor_id": current_user.id}
    )
    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("dashboard"))

    profile_path = None
    if student.get("profile_photo"):
        # e.g. static/images/students/deeksha.jpg on disk
        profile_path = os.path.abspath(os.path.join("static", student["profile_photo"]))
        profile_path = profile_path.replace("\\", "/")

    logo_path = os.path.abspath(os.path.join("static", "images", "logo.png"))
    logo_path = logo_path.replace("\\", "/")

    print("PROFILE FILE:", profile_path)
    print("LOGO FILE:", logo_path)

    html = render_template(
        "report_pdf.html",
        student=student,
        profile_path=profile_path,
        logo_path=logo_path
    )
    pdf_bytes = HTML(string=html).write_pdf()

    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=f"{student['student_name']}_report.pdf",
        mimetype="application/pdf"
    )


@app.route("/student/<student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    db.students.delete_one({"_id": ObjectId(student_id), "professor_id": current_user.id})
    flash("Student report deleted", "info")
    return redirect(url_for("dashboard"))
