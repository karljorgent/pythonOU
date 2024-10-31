from app import create_app, db
from app.models import Company, NaturalPerson, LegalPerson, Shareholder
from datetime import datetime, date

app = create_app()

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        persons = [
            NaturalPerson(
                first_name='Mari',
                last_name='Maasikas',
                identification_code='47101010033'
            ),
            NaturalPerson(
                first_name='Jaan',
                last_name='Jõgi',
                identification_code='37202020044'
            ),
            LegalPerson(
                company_name='Investeeringud OÜ',
                identification_code='1234567'
            )
        ]
        
        for person in persons:
            db.session.add(person)
        
        company = Company(
            name='Näidis OÜ',
            registry_code='1234567',
            founding_date=date(2024, 1, 1),
            share_capital=2500
        )
        db.session.add(company)
        
        db.session.commit()
        
        shareholders = [
            Shareholder(
                company_id=company.id,
                person_id=persons[0].id,
                share_size=1500,
                is_founder=True
            ),
            Shareholder(
                company_id=company.id,
                person_id=persons[1].id,
                share_size=1000,
                is_founder=True
            )
        ]
        
        for shareholder in shareholders:
            db.session.add(shareholder)
        
        db.session.commit()
        
        print("Andmebaas on täidetud näidisandmetega!")

if __name__ == '__main__':
    init_db()