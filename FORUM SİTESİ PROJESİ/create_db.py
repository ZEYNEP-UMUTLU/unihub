from app import app, db

with app.app_context():
    db.drop_all()  # Önce tüm tabloları temizle
    db.create_all()
    print("Tüm tablolar başarıyla oluşturuldu.")