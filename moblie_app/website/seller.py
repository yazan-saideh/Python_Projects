import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Estate, EstateImage
from . import db
from datetime import datetime

seller = Blueprint('seller', __name__)

# Folder where you want to save uploaded images
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'website', 'static')  # Use absolute path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@seller.route('/')
@login_required
def seller_home():
    return render_template("seller.html", user=current_user)


@seller.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'rent':
            return redirect(url_for('seller.rent_house'))
        elif action == 'sell':
            return redirect(url_for('seller.sell_house'))
    return render_template('add_product.html', user=current_user)


@seller.route('/sell-house', methods=['GET', 'POST'])
@login_required
def sell_house():
    if request.method == 'POST':
        # Get form data
        price = request.form.get('price')
        size = request.form.get('size')
        location = request.form.get('location')
        bedrooms = request.form.get('bedrooms')
        bathrooms = request.form.get('bathrooms')
        property_type = request.form.get('property_type')
        garage = request.form.get('garage') == 'yes'
        created_at_str = request.form.get('created_at')
        created_at = datetime.strptime(created_at_str, '%Y-%m-%d') if created_at_str else None
        files = request.files.getlist('images')  # Get the list of uploaded files

        # Validation checks
        if not price or not size or not location or not bedrooms or not bathrooms or not files:
            flash('Please fill in all required fields and upload at least one image.', category='error')
            return redirect(url_for('seller.sell_house'))

        # Create and save the Estate object first
        new_estate = Estate(
            price=price,
            size=size,
            location=location,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            garage=garage,
            property_type=property_type,
            created_at=created_at,
            seller_id=current_user.id,
        )

        db.session.add(new_estate)
        db.session.commit()  # Save the estate to get the estate_id

        # Now save the images associated with this estate
        for file in files:
            if allowed_file(file.filename):
                try:
                    # Ensure the upload folder exists
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)

                    # Secure the filename and append a timestamp to ensure uniqueness
                    filename = secure_filename(file.filename)
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

                    # Save the file to the specified path
                    file.save(file_path)

                    # Create a new EstateImage object and associate it with the estate
                    estate_image = EstateImage(
                        estate_id=new_estate.id,  # Use the saved estate's ID
                        image_filename=unique_filename
                    )
                    db.session.add(estate_image)  # Add image to the session

                except Exception as e:
                    flash(f'Error saving the file: {str(e)}', category='error')
                    db.session.rollback()  # Rollback the session in case of an error
                    return redirect(url_for('seller.sell_house'))
            else:
                flash('Invalid image format. Please upload only PNG, JPG, or JPEG.', category='error')
                db.session.rollback()  # Rollback the session in case of an error
                return redirect(url_for('seller.sell_house'))

        # Commit all changes
        db.session.commit()

        flash('House added successfully!', category='success')
        return redirect(url_for('seller.seller_home'))

    return render_template('sell_house.html', user=current_user)

@seller.route('/manage_inventory', methods=['GET', 'POST'])
@login_required
def manage_inventory():
    estates = Estate.query.filter_by(seller_id=current_user.id).all()
    default_image = 'default_image.png'

    if request.method == 'POST':
        # Handle estate deletion
        if 'delete_estate' in request.form:
            estate_id = int(request.form.get('delete_estate'))
            estate = Estate.query.get(estate_id)

            if estate and estate.seller_id == current_user.id:
                # Remove associated images from the filesystem
                for image in estate.images:
                    try:
                        os.remove(os.path.join(UPLOAD_FOLDER, image.image_filename))
                    except FileNotFoundError:
                        pass  # Image file doesn't exist, so just ignore this step

                db.session.delete(estate)
                db.session.commit()
                flash('Estate deleted successfully!', category='success')
            else:
                flash('Estate not found or you do not have permission to delete it.', category='error')
            return redirect(url_for('seller.manage_inventory'))

        # Handle estate updates
        if 'update_estate' in request.form:
            estate_id = int(request.form.get('update_estate'))
            estate = Estate.query.get(estate_id)

            if estate and estate.seller_id == current_user.id:
                estate.price = request.form.get('new_price')
                estate.location = request.form.get('new_location')
                estate.size = request.form.get('new_size')
                estate.bedrooms = request.form.get('new_bedrooms')
                estate.bathrooms = request.form.get('new_bathrooms')
                estate.garage = request.form.get('new_garage') == '1'

                # Handle image uploads if new images are provided
                new_files = request.files.getlist('new_image')  # Get all uploaded files
                for new_file in new_files:
                    if new_file and allowed_file(new_file.filename):
                        # Save the new image
                        new_filename = secure_filename(new_file.filename)
                        unique_new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{new_filename}"
                        new_file_path = os.path.join(UPLOAD_FOLDER, unique_new_filename)
                        new_file.save(new_file_path)

                        # Create a new EstateImage record
                        new_image = EstateImage(image_filename=unique_new_filename, estate=estate)
                        db.session.add(new_image)  # Add the new image to the session

                db.session.commit()
                flash('Estate updated successfully!', category='success')
            else:
                flash('Estate not found or you do not have permission to update it.', category='error')

            return redirect(url_for('seller.manage_inventory'))

    for estate in estates:
        print(f"Estate ID: {estate.id}, Images: {[image.image_filename for image in estate.images]}")

    return render_template('manage_inventory.html', estates=estates, user=current_user)