from flask import render_template, request, redirect, url_for, flash, current_app as app
from app.models import Company, Person, Shareholder, NaturalPerson, LegalPerson
from app import db
from datetime import datetime, date
from sqlalchemy import or_

def validate_company_data(data):
    """Validate company input data"""
    errors = []
    
    if not 3 <= len(data.get('name', '')) <= 100:
        errors.append('Nimi peab olema 3 kuni 100 tähemärki pikk')
    if not data.get('name', '').replace(' ', '').isalnum():
        errors.append('Nimi võib sisaldada ainult tähti, numbreid ja tühikuid')
    
    registry_code = data.get('registry_code', '')
    if not (registry_code.isdigit() and len(registry_code) == 7):
        errors.append('Registrikood peab olema 7-kohaline number')
    
    try:
        founding_date = datetime.strptime(data.get('founding_date', ''), '%Y-%m-%d').date()
        if founding_date > date.today():
            errors.append('Asutamiskuupäev ei saa olla tulevikus')
    except ValueError:
        errors.append('Vigane kuupäev')
    
    try:
        share_capital = int(data.get('share_capital', 0))
        if share_capital < 2500:
            errors.append('Osakapital peab olema vähemalt 2500 EUR')
    except ValueError:
        errors.append('Vigane osakapitali summa')
    
    return errors

def validate_shareholders_data(shareholders_data, shares_data, total_capital):
    """Validate shareholders input data"""
    errors = []
    
    if not shareholders_data or not shares_data:
        errors.append('Vähemalt üks osanik on kohustuslik')
        return errors
        
    try:
        shares = [int(share) for share in shares_data if share]
        
        if any(share <= 0 for share in shares):
            errors.append('Osa suurus peab olema positiivne number')
        
        total_shares = sum(shares)
        if total_shares != total_capital:
            errors.append(f'Osade summa ({total_shares}) ei võrdu osakapitaliga ({total_capital})')
        
        if len(set(shareholders_data)) != len(shareholders_data):
            errors.append('Sama osanik on lisatud mitu korda')
            
    except ValueError:
        errors.append('Vigane osa suurus')
    
    return errors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    search_type = request.args.get('type', 'company')
    
    if search_type == 'company':
        results = Company.query.filter(
            or_(
                Company.name.ilike(f'%{query}%'),
                Company.registry_code.ilike(f'%{query}%')
            )
        ).all()
    else:
        results = Person.query.filter(
            or_(
                Person.first_name.ilike(f'%{query}%'),
                Person.last_name.ilike(f'%{query}%'),
                Person.identification_code.ilike(f'%{query}%')
            )
        ).all()
    
    return render_template('search_results.html', results=results)

@app.route('/company/<int:id>')
def view_company(id):
    company = Company.query.get_or_404(id)
    return render_template('company_view.html', company=company)

@app.route('/company/new', methods=['GET', 'POST'])
def new_company():
    if request.method == 'POST':
        
        company_errors = validate_company_data(request.form)
        
        shareholders_data = request.form.getlist('shareholder')
        shares_data = request.form.getlist('share_size')
        share_capital = int(request.form.get('share_capital', 0))
        
        shareholder_errors = validate_shareholders_data(
            shareholders_data, 
            shares_data, 
            share_capital
        )
        
        if Company.query.filter_by(registry_code=request.form.get('registry_code')).first():
            company_errors.append('See registrikood on juba kasutusel')
        
        if company_errors or shareholder_errors:
            for error in company_errors + shareholder_errors:
                flash(error)
            return redirect(url_for('new_company'))
        
        try:
            company = Company(
                name=request.form['name'],
                registry_code=request.form['registry_code'],
                founding_date=datetime.strptime(request.form['founding_date'], '%Y-%m-%d').date(),
                share_capital=share_capital
            )
            
            db.session.add(company)
            db.session.commit()
            
            for person_id, share_size in zip(shareholders_data, shares_data):
                shareholder = Shareholder(
                    company_id=company.id,
                    person_id=int(person_id),
                    share_size=int(share_size),
                    is_founder=True
                )
                db.session.add(shareholder)
            
            db.session.commit()
            flash('Osaühing edukalt loodud!')
            return redirect(url_for('view_company', id=company.id))
            
        except Exception as e:
            db.session.rollback()
            flash('Viga osaühingu loomisel: ' + str(e))
            return redirect(url_for('new_company'))
            
    persons = Person.query.all()
    return render_template('company_form.html', 
                         persons=persons, 
                         today=date.today().strftime('%Y-%m-%d'))

@app.route('/company/<int:id>/increase-capital', methods=['GET', 'POST'])
def increase_capital(id):
    company = Company.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            shareholders_data = request.form.getlist('shareholder')
            shares_data = request.form.getlist('share_size')
            
            if not shareholders_data or not shares_data:
                flash('Vähemalt üks osa on vajalik')
                return redirect(url_for('increase_capital', id=id))
            
            try:
                shares = [int(share) for share in shares_data]
                if all(share == 0 for share in shares):
                    flash('Vähemalt ühe osaniku osa peab muutuma')
                    return redirect(url_for('increase_capital', id=id))
            except ValueError:
                flash('Vigane osa suurus')
                return redirect(url_for('increase_capital', id=id))
            
            if len(set(shareholders_data)) != len(shareholders_data):
                flash('Sama osanik on lisatud mitu korda')
                return redirect(url_for('increase_capital', id=id))
            
            total_change = 0
            for person_id, share_change in zip(shareholders_data, shares):
                share_change = int(share_change)
                if share_change != 0:
                    existing_shareholder = Shareholder.query.filter_by(
                        company_id=company.id,
                        person_id=int(person_id)
                    ).first()
                    
                    if existing_shareholder:
                        new_size = existing_shareholder.share_size + share_change
                        if new_size < 0:
                            flash(f'Osaniku osa ei saa olla negatiivne')
                            return redirect(url_for('increase_capital', id=id))
                        existing_shareholder.share_size = new_size
                    else:
                        if share_change <= 0:
                            flash('Uue osaniku osa peab olema positiivne')
                            return redirect(url_for('increase_capital', id=id))
                        shareholder = Shareholder(
                            company_id=company.id,
                            person_id=int(person_id),
                            share_size=share_change,
                            is_founder=False
                        )
                        db.session.add(shareholder)
                    
                    total_change += share_change
            
            if total_change == 0:
                flash('Ühtegi muudatust ei tehtud')
                return redirect(url_for('increase_capital', id=id))
                
            company.share_capital += total_change
            
            db.session.commit()
            flash('Osakapital edukalt muudetud!')
            return redirect(url_for('view_company', id=company.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Viga osakapitali muutmisel: {str(e)}')
            return redirect(url_for('increase_capital', id=id))
            
    persons = Person.query.all()
    return render_template('increase_capital.html', company=company, persons=persons)