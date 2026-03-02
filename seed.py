print("=== SEED SCRIPT STARTING ===")
import sys, os
print(f"Python: {sys.executable}")
print(f"Working dir: {os.getcwd()}")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
print("sys.path updated")

try:
    print("Importing config...")
    from app.core.config import settings
    print(f"DB URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"ERROR importing config: {e}")
    sys.exit(1)

try:
    print("Importing database...")
    from app.core.database import SessionLocal, engine, Base
    print("Database imported OK")
except Exception as e:
    print(f"ERROR importing database: {e}")
    sys.exit(1)

try:
    print("Importing security...")
    from app.core.security import hash_password
    print("Security imported OK")
except Exception as e:
    print(f"ERROR importing security: {e}")
    sys.exit(1)

try:
    print("Importing models...")
    from app.models.user     import User, UserRole
    from app.models.product import Category
    from app.models.product  import Product
    from app.models.order    import Order, OrderItem
    from app.models.order  import Address, CartItem, Wishlist
    print("Models imported OK")
except Exception as e:
    print(f"ERROR importing models: {e}")
    sys.exit(1)

try:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created OK")
except Exception as e:
    print(f"ERROR creating tables: {e}")
    sys.exit(1)

try:
    print("Opening DB session...")
    db = SessionLocal()
    print("DB session opened OK")
    
    count = db.query(User).count()
    print(f"Current user count: {count}")
    db.close()
except Exception as e:
    print(f"ERROR with DB session: {e}")
    sys.exit(1)

print("=== ALL IMPORTS OK — RUNNING SEEDER ===")

# ── Now the actual seeding ────────────────────────────────────────────────────

db = SessionLocal()

def seed_users():
    print("\n🌱 Seeding users...")
    if db.query(User).first():
        print("   ⚠️  Users already exist, skipping.")
        return

    users = [
        User(
            name        = "Admin",
            email       = "admin@gmail.com",
            password    = hash_password("Admin@123"),
            phone       = "+91-98765-43210",
            role        = UserRole.admin,
            avatar      = "https://i.pravatar.cc/150?img=1",
            is_active   = True,
            is_verified = True,
        ),
        User(
            name        = "User1",
            email       = "user1@gmail.com",
            password    = hash_password("User1@123"),
            phone       = "+91-91234-56789",
            role        = UserRole.user,
            avatar      = "https://i.pravatar.cc/150?img=5",
            is_active   = True,
            is_verified = True,
        ),
        User(
            name        = "User2",
            email       = "user2@gmail.com",
            password    = hash_password("User2@123"),
            phone       = "+91-99887-76655",
            role        = UserRole.user,
            avatar      = "https://i.pravatar.cc/150?img=3",
            is_active   = True,
            is_verified = True,
        ),
    ]

    db.add_all(users)
    db.commit()
    print(f"   ✅ {len(users)} users created.")


def seed_categories():
    print("\n🌱 Seeding categories...")
    if db.query(Category).first():
        print("   ⚠️  Categories already exist, skipping.")
        return

    categories = [
        Category(name="Electronics",    slug="electronics", icon="📱", product_count=0),
        Category(name="Clothing",       slug="clothing",    icon="👗", product_count=0),
        Category(name="Books",          slug="books",       icon="📚", product_count=0),
        Category(name="Home & Kitchen", slug="home-garden", icon="🏠", product_count=0),
        Category(name="Sports",         slug="sports",      icon="🏏", product_count=0),
        Category(name="Beauty",         slug="beauty",      icon="💄", product_count=0),
    ]

    db.add_all(categories)
    db.commit()
    print(f"   ✅ {len(categories)} categories created.")


def seed_addresses():
    print("\n🌱 Seeding addresses...")
    if db.query(Address).first():
        print("   ⚠️  Addresses already exist, skipping.")
        return

    priya = db.query(User).filter(User.email == "user1@gmail.com").first()
    arjun = db.query(User).filter(User.email == "user2@gmail.com").first()

    if not priya or not arjun:
        print("   ❌ Users not found, seed users first!")
        return

    addresses = [
        Address(
            user_id    = priya.id,
            label      = "Home",
            full_name  = "User1",
            street     = "12, Vastrapur, Near Ahmedabad University",
            city       = "Ahmedabad",
            state      = "Gujarat",
            zip        = "380015",
            country    = "India",
            phone      = "+91-91234-56789",
            is_default = True,
        ),
        Address(
            user_id    = priya.id,
            label      = "Work",
            full_name  = "User1",
            street     = "501, Shapath Hexa, SG Highway",
            city       = "Ahmedabad",
            state      = "Gujarat",
            zip        = "380060",
            country    = "India",
            phone      = "+91-91234-56789",
            is_default = False,
        ),
        Address(
            user_id    = arjun.id,
            label      = "Home",
            full_name  = "User2",
            street     = "42, Bandra West, Linking Road",
            city       = "Mumbai",
            state      = "Maharashtra",
            zip        = "400050",
            country    = "India",
            phone      = "+91-99887-76655",
            is_default = True,
        ),
    ]

    db.add_all(addresses)
    db.commit()
    print(f"   ✅ {len(addresses)} addresses created.")


def seed_products():
    print("\n🌱 Seeding products...")
    if db.query(Product).first():
        print("   ⚠️  Products already exist, skipping.")
        return

    def cat_id(slug):
        c = db.query(Category).filter(Category.slug == slug).first()
        return c.id if c else None

    products_data = [
        dict(name="Samsung Galaxy S24 Ultra",          category="electronics", price=129999, discount=10, stock=30,  rating=4.8, reviews=4200,  is_featured=True,  image="https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400"),
        dict(name="OnePlus 12R",                       category="electronics", price=44999,  discount=0,  stock=50,  rating=4.7, reviews=3100,  is_featured=True,  image="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400"),
        dict(name="boAt Rockerz 550 Headphones",       category="electronics", price=1999,   discount=15, stock=200, rating=4.5, reviews=8900,  is_featured=True,  image="https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400"),
        dict(name="Redmi Note 13 Pro",                 category="electronics", price=26999,  discount=0,  stock=80,  rating=4.6, reviews=5600,  is_featured=True,  image="https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400"),
        dict(name="Apple iPad 10th Generation",        category="electronics", price=59900,  discount=5,  stock=40,  rating=4.8, reviews=2100,  is_featured=True,  image="https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400"),
        dict(name="Fire-Boltt Ninja Smartwatch",       category="electronics", price=1499,   discount=20, stock=300, rating=4.4, reviews=12000, is_featured=False, image="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"),
        dict(name="Fabindia Cotton Kurta Set",         category="clothing",    price=2499,   discount=10, stock=150, rating=4.6, reviews=3400,  is_featured=True,  image="https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=400"),
        dict(name="Biba Anarkali Suit",                category="clothing",    price=3299,   discount=0,  stock=100, rating=4.5, reviews=2200,  is_featured=False, image="https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400"),
        dict(name="Raymond Regular Fit Shirt",         category="clothing",    price=1799,   discount=0,  stock=200, rating=4.4, reviews=1800,  is_featured=False, image="https://images.unsplash.com/photo-1603252109303-2751441dd157?w=400"),
        dict(name="Jockey Mens T-Shirt Pack of 3",     category="clothing",    price=999,    discount=15, stock=400, rating=4.3, reviews=9800,  is_featured=False, image="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"),
        dict(name="Wings of Fire APJ Abdul Kalam",     category="books",       price=199,    discount=0,  stock=500, rating=4.9, reviews=25000, is_featured=False, image="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400"),
        dict(name="The 3 Mistakes of My Life",         category="books",       price=249,    discount=10, stock=400, rating=4.7, reviews=18000, is_featured=False, image="https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400"),
        dict(name="Rich Dad Poor Dad",                 category="books",       price=299,    discount=0,  stock=600, rating=4.8, reviews=32000, is_featured=False, image="https://images.unsplash.com/photo-1589998059171-988d887df646?w=400"),
        dict(name="Atomic Habits",                     category="books",       price=349,    discount=5,  stock=300, rating=4.9, reviews=28000, is_featured=False, image="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400"),
        dict(name="Prestige Electric Pressure Cooker", category="home-garden", price=3499,   discount=10, stock=75,  rating=4.7, reviews=6700,  is_featured=False, image="https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400"),
        dict(name="Bajaj 45L Tower Air Cooler",        category="home-garden", price=11999,  discount=15, stock=40,  rating=4.5, reviews=3200,  is_featured=False, image="https://images.unsplash.com/photo-1628177142898-93e36e4e3a50?w=400"),
        dict(name="Nivia Pro Yoga Mat",                category="sports",      price=899,    discount=0,  stock=150, rating=4.5, reviews=4500,  is_featured=False, image="https://images.unsplash.com/photo-1601925228792-8a0a21e49bef?w=400"),
        dict(name="SG Scorer Cricket Bat",             category="sports",      price=2199,   discount=0,  stock=80,  rating=4.6, reviews=2800,  is_featured=False, image="https://images.unsplash.com/photo-1531415074968-036ba1b575da?w=400"),
        dict(name="Mamaearth Ubtan Face Wash",         category="beauty",      price=299,    discount=10, stock=800, rating=4.7, reviews=15000, is_featured=False, image="https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400"),
        dict(name="Biotique Bio Sunscreen SPF 40",     category="beauty",      price=199,    discount=0,  stock=600, rating=4.5, reviews=9200,  is_featured=False, image="https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=400"),
    ]

    products = []
    for p in products_data:
        slug = p['name'].lower()
        slug = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in slug)
        slug = '-'.join(slug.split())

        product = Product(
            name           = p['name'],
            slug           = slug,
            description    = f"Premium quality {p['name']}. Trusted by millions of Indian customers. Comes with manufacturer warranty and excellent customer support.",
            price          = p['price'],
            discount       = p['discount'],
            stock          = p['stock'],
            rating         = p['rating'],
            reviews        = p['reviews'],
            sold           = p['reviews'] // 3,
            image          = p['image'],
            images         = [p['image']],
            category       = p['category'],
            category_id    = cat_id(p['category']),
            tags           = [p['category'], 'popular'],
            specifications = {
                'Brand':    p['name'].split(' ')[0],
                'Category': p['category'],
                'Warranty': '1 Year',
                'In Stock': 'Yes' if p['stock'] > 0 else 'No',
            },
            is_featured = p.get('is_featured', False),
            is_new      = False,
            is_active   = True,
        )
        products.append(product)

    db.add_all(products)
    db.commit()

    # Update category counts
    for cat in db.query(Category).all():
        count = db.query(Product).filter(Product.category == cat.slug).count()
        cat.product_count = count
    db.commit()

    print(f"   ✅ {len(products)} products created.")


def seed_orders():
    print("\n🌱 Seeding sample orders...")
    if db.query(Order).first():
        print("   ⚠️  Orders already exist, skipping.")
        return

    priya   = db.query(User).filter(User.email == "user1@gmail.com").first()
    address = db.query(Address).filter(
        Address.user_id    == priya.id,
        Address.is_default == True
    ).first()
    galaxy  = db.query(Product).filter(Product.name == "Samsung Galaxy S24 Ultra").first()
    boat    = db.query(Product).filter(Product.name == "boAt Rockerz 550 Headphones").first()
    kurta   = db.query(Product).filter(Product.name == "Fabindia Cotton Kurta Set").first()

    if not all([priya, address, galaxy, boat, kurta]):
        print("   ❌ Required data not found, skipping orders.")
        return

    address_snapshot = {
        "full_name": address.full_name,
        "street":    address.street,
        "city":      address.city,
        "state":     address.state,
        "zip":       address.zip,
        "country":   address.country,
    }

    order1 = Order(
        order_number   = "ORD-2024-000001",
        user_id        = priya.id,
        status         = "delivered",
        subtotal       = 131998,
        shipping       = 0,
        tax            = 23759,
        total          = 155757,
        payment_method = "UPI",
        payment_status = "paid",
        address        = address_snapshot,
        tracking       = [
            {"status": "Order Placed",     "date": "2024-12-01T10:30:00Z", "done": True},
            {"status": "Processing",       "date": "2024-12-01T14:00:00Z", "done": True},
            {"status": "Shipped",          "date": "2024-12-02T09:00:00Z", "done": True},
            {"status": "Out for Delivery", "date": "2024-12-03T08:00:00Z", "done": True},
            {"status": "Delivered",        "date": "2024-12-03T14:00:00Z", "done": True},
        ],
        items = [
            OrderItem(product_id=galaxy.id, name=galaxy.name, price=galaxy.price, quantity=1, image=galaxy.image),
            OrderItem(product_id=boat.id,   name=boat.name,   price=boat.price,   quantity=1, image=boat.image),
        ]
    )

    order2 = Order(
        order_number   = "ORD-2024-000002",
        user_id        = priya.id,
        status         = "shipped",
        subtotal       = 4998,
        shipping       = 99,
        tax            = 899,
        total          = 5996,
        payment_method = "Net Banking",
        payment_status = "paid",
        address        = address_snapshot,
        tracking       = [
            {"status": "Order Placed",     "date": "2024-12-10T15:00:00Z", "done": True},
            {"status": "Processing",       "date": "2024-12-10T18:00:00Z", "done": True},
            {"status": "Shipped",          "date": "2024-12-11T10:00:00Z", "done": True},
            {"status": "Out for Delivery", "date": None,                   "done": False},
            {"status": "Delivered",        "date": None,                   "done": False},
        ],
        items = [
            OrderItem(product_id=kurta.id, name=kurta.name, price=kurta.price, quantity=2, image=kurta.image),
        ]
    )

    db.add_all([order1, order2])
    db.commit()
    print("   ✅ 2 sample orders created.")


# ── Main ──────────────────────────────────────────────────────────────────────
print("\n🚀 Starting database seeding...\n")
try:
    seed_users()
    seed_categories()
    seed_addresses()
    seed_products()
    seed_orders()
    print("\n✅ Database seeded successfully!")
    print("\n" + "─" * 42)
    print("  Credentials")
    print("─" * 42)
    print("  Admin → admin@shopelite.in  / Admin@123")
    print("  User  → user1@gmail.com   / Priya@123")
    print("  User  → user2@gmail.com   / Arjun@123")
    print("─" * 42 + "\n")
except Exception as e:
    db.rollback()
    print(f"\n❌ Seeding failed!")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()