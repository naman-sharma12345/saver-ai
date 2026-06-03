"""
Train the expense category classifier.

Generates a synthetic dataset of 500+ student expense descriptions,
trains a TF-IDF + LinearSVC pipeline with GridSearchCV hyperparameter
tuning, evaluates accuracy, and persists the best model.

Usage:
    python ml/train_category_model.py
"""

import os
import sys
import random
import logging

import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import classification_report, accuracy_score

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'category_classifier.pkl')
CSV_PATH = os.path.join(BASE_DIR, 'expense_data.csv')


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic data templates per category
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATES = {
    'Food': [
        'zomato order', 'swiggy delivery', 'lunch at canteen', 'dinner at restaurant',
        'pizza from dominos', 'burger at mcdonalds', 'biryani order', 'coffee at starbucks',
        'tea and snacks', 'mess monthly fee', 'bakery pastry', 'juice from fresh bar',
        'maggi from store', 'momos street food', 'samosa and chai', 'chaat at stall',
        'thali at dhaba', 'dosa at south indian restaurant', 'idli vada breakfast',
        'paratha with curd', 'noodles from chinese stall', 'ice cream sundae',
        'cake for birthday', 'brownie from cafe', 'sandwich from subway',
        'wrap at college cafeteria', 'egg roll from stall', 'soup at restaurant',
        'salad from fresh menu', 'milkshake keventers', 'lassi from lassi shop',
        'paneer butter masala dinner', 'dal rice meal', 'roti sabzi lunch',
        'naan with gravy', 'kulcha chole', 'chole bhature', 'pav bhaji street food',
        'vada pav snack', 'french fries mcdonalds', 'combo meal kfc',
        'chicken wings order', 'pasta at cafe', 'risotto at restaurant',
        'sushi order online', 'butter chicken dinner', 'rajma chawal lunch',
        'poha jalebi breakfast', 'upma for morning', 'fruit bowl from vendor',
        'coconut water from stall', 'cold drink pepsi', 'mineral water bottle',
        'chips packet from store', 'biscuits parle g', 'chocolate dairy milk',
        'protein bar snack', 'energy drink redbull', 'smoothie berry blast',
        'pancake breakfast cafe', 'waffle with syrup', 'donut from dunkin',
        'muffin chocolate', 'garlic bread dominos', 'spring roll chinese',
        'manchurian from stall', 'fried rice takeaway', 'dal makhani dinner',
        'paneer tikka starter', 'chicken tikka order', 'fish fry dinner',
        'kebab from restaurant', 'shawarma roll street', 'falafel wrap',
    ],
    'Transport': [
        'uber ride to college', 'ola cab booking', 'auto rickshaw fare',
        'metro card recharge', 'bus ticket purchase', 'rapido bike taxi',
        'petrol for bike', 'diesel for car', 'parking charges mall',
        'toll plaza charges', 'train ticket booking', 'flight ticket',
        'local train pass', 'uber pool ride', 'ola share cab',
        'auto to market', 'metro token purchase', 'bus pass monthly',
        'cab to airport', 'taxi from station', 'rickshaw to hostel',
        'bike fuel top up', 'scooter petrol fill', 'parking lot fee',
        'highway toll payment', 'train reservation', 'tatkal train ticket',
        'rapido auto booking', 'indriver cab fare', 'shuttle bus college',
        'cycle repair shop', 'tire puncture repair', 'bike service center',
        'vehicle insurance payment', 'pollution check certificate',
        'driving school fees', 'car wash service', 'battery replacement vehicle',
        'engine oil change', 'uber eats delivery charge', 'cab surge pricing night',
        'metro smart card recharge', 'bus fare city transport', 'auto meter fare',
        'airport shuttle fare', 'rental car charges', 'ola outstation trip',
        'interstate bus ticket', 'volvo bus booking', 'sleeper bus journey',
        'shared auto morning', 'e rickshaw ride', 'toto ride campus',
        'ferry boat ticket', 'cable car ride', 'funicular railway fare',
        'helicopter tour booking', 'cruise ship ticket', 'yacht rental',
        'bike rental hourly', 'scooter sharing bounce', 'yulu cycle ride',
        'uber go ride home', 'ola prime sedan', 'meru cab airport',
    ],
    'Study Materials': [
        'textbook purchase', 'notebook and pens', 'xerox copies notes',
        'udemy course purchase', 'stationery supplies', 'photocopy assignment',
        'coursera subscription', 'library fine payment', 'printing project report',
        'reference book purchase', 'highlighter markers', 'scientific calculator',
        'lab manual purchase', 'project materials hardware', 'graph paper sheets',
        'compass geometry set', 'pencil eraser set', 'file folder organizer',
        'whiteboard markers', 'chart paper project', 'sticky notes pack',
        'stapler and pins', 'punching machine buy', 'glue stick fevicol',
        'sketch pens color', 'drawing sheet A3', 'tracing paper roll',
        'usb drive flash', 'hard disk external', 'laptop charger replacement',
        'mouse wireless buy', 'keyboard replacement', 'screen protector laptop',
        'coding bootcamp fee', 'online certification exam', 'aws certification voucher',
        'skillshare subscription', 'linkedin learning monthly', 'edx course fee',
        'pluralsight annual plan', 'hackerrank premium', 'leetcode premium subscription',
        'chegg study subscription', 'grammarly premium', 'turnitin access',
        'research paper access', 'journal subscription ieee', 'matlab license',
        'autocad student license', 'adobe creative cloud', 'microsoft office 365',
        'zoom pro subscription', 'notion premium plan', 'evernote subscription',
        'ink cartridge printer', 'toner refill laser', 'paper ream A4',
        'binding spiral book', 'lamination sheets', 'poster printing large',
        'banner for presentation', 'model making supplies', 'breadboard electronics',
        'arduino kit purchase', 'raspberry pi board', 'sensors kit robotics',
        'chemistry lab supplies', 'biology specimen slides', 'physics experiment kit',
    ],
    'Entertainment': [
        'netflix subscription monthly', 'spotify premium plan', 'movie ticket pvr',
        'movie ticket inox', 'gaming credits purchase', 'concert ticket booking',
        'party expenses club', 'amazon prime annual', 'hotstar subscription',
        'disney plus monthly', 'youtube premium plan', 'bowling alley outing',
        'amusement park tickets', 'water park entry', 'escape room game',
        'board game purchase', 'playstation game buy', 'xbox game pass',
        'steam game purchase', 'mobile game in app', 'pubg uc purchase',
        'valorant skin buy', 'spotify family plan', 'apple music subscription',
        'jio cinema premium', 'zee5 annual plan', 'voot select monthly',
        'sonyliv subscription', 'mubi film streaming', 'crunchyroll anime',
        'twitch subscription streamer', 'discord nitro monthly', 'karaoke night',
        'comedy show tickets', 'stand up comedy', 'theatre play tickets',
        'museum entry fee', 'art gallery visit', 'paintball game session',
        'laser tag game', 'go karting racing', 'trampoline park entry',
        'billiards pool game', 'cricket match tickets', 'ipl tickets stadium',
        'football match viewing', 'sports bar tab', 'pub night out',
        'lounge entry fee', 'hookah cafe session', 'picnic outing expenses',
        'trekking trip entry', 'camping gear rental', 'beach outing food',
        'road trip fuel snacks', 'weekend getaway hotel', 'birthday party decoration',
        'halloween costume buy', 'diwali crackers', 'holi colors purchase',
        'new year party tickets', 'valentines day dinner', 'anniversary celebration',
        'surprise party arrangement', 'gift wrapping supplies', 'balloon decoration',
        'dj booking party', 'karaoke machine rental', 'photo booth rental',
    ],
    'Shopping': [
        'amazon order electronics', 'flipkart purchase', 'myntra clothes order',
        'nike shoes purchase', 'flipkart big billion', 'amazon great sale',
        'watch purchase online', 'backpack bag new', 'wireless headphones',
        'bluetooth earbuds', 'phone case cover', 'laptop accessories buy',
        't shirt new', 'jeans denim purchase', 'jacket winter buy',
        'hoodie sweatshirt', 'formal shirt office', 'trouser formal wear',
        'kurta ethnic wear', 'saree for function', 'salwar suit purchase',
        'sunglasses rayban', 'belt leather new', 'wallet leather buy',
        'perfume purchase', 'deodorant axe spray', 'grooming kit set',
        'trimmer philips buy', 'razor shaving kit', 'face wash nivea',
        'moisturizer cream', 'shampoo conditioner', 'hair oil purchase',
        'toothbrush colgate', 'toothpaste sensodyne', 'soap body wash',
        'towel bath new', 'bedsheet pillow cover', 'curtains window',
        'table lamp study', 'wall clock purchase', 'photo frame buy',
        'decorative items room', 'plant pot indoor', 'fairy lights string',
        'extension board electrical', 'charger cable usb', 'power bank buy',
        'smart watch fitness', 'fitness band purchase', 'weighing scale digital',
        'water bottle flask', 'lunch box container', 'umbrella purchase',
        'rain coat buy', 'slippers flip flops', 'sandals casual wear',
        'sports shoes running', 'gym gloves buy', 'yoga mat purchase',
        'resistance band set', 'dumbbell home gym', 'skipping rope fitness',
        'cricket bat purchase', 'football buy', 'badminton racket set',
        'swimming goggles cap', 'cycling shorts', 'track pants joggers',
    ],
    'Bills': [
        'electricity bill payment', 'water bill monthly', 'internet wifi bill',
        'mobile recharge prepaid', 'phone bill postpaid', 'room rent monthly',
        'hostel maintenance fee', 'insurance premium health', 'emi payment loan',
        'education loan emi', 'bike loan emi', 'subscription renewal annual',
        'gas cylinder refill', 'newspaper delivery monthly', 'laundry service monthly',
        'gym membership monthly', 'club membership fee', 'society maintenance',
        'property tax payment', 'income tax filing', 'gst payment business',
        'credit card bill', 'broadband bill monthly', 'dth recharge tata',
        'cable tv bill', 'landline phone bill', 'cloud storage google',
        'icloud storage apple', 'vpn subscription annual', 'antivirus license',
        'domain hosting renewal', 'server hosting monthly', 'app subscription fee',
        'music subscription bill', 'ott platform bill', 'news subscription digital',
        'magazine subscription', 'pg room rent', 'flat sharing rent',
        'apartment rent monthly', 'water purifier service', 'ac service maintenance',
        'refrigerator repair bill', 'washing machine service', 'inverter battery replace',
        'ups maintenance charge', 'solar panel emi', 'security deposit advance',
        'pest control service', 'plumber service call', 'electrician service home',
        'carpenter furniture repair', 'painter wall service', 'cleaner domestic help',
        'cook salary monthly', 'driver salary payment', 'gardener charges monthly',
        'parking slot monthly', 'toll pass fastag', 'municipal tax payment',
        'fire insurance annual', 'life insurance premium', 'vehicle insurance renewal',
        'jio fiber monthly', 'airtel broadband bill', 'bsnl landline bill',
    ],
    'Health': [
        'medicine from pharmacy', 'doctor consultation fee', 'gym membership annual',
        'dental checkup visit', 'apollo pharmacy purchase', 'eye checkup ophthalmologist',
        'medical test blood', 'fitness equipment buy', 'hospital visit charges',
        'prescription medicines refill', 'protein powder supplement', 'vitamin tablets',
        'omega 3 fish oil', 'calcium supplement tabs', 'multivitamin daily',
        'physiotherapy session', 'chiropractor appointment', 'dermatologist visit',
        'skin care treatment', 'acne medication cream', 'hair fall treatment',
        'allergy medicine antihistamine', 'cold flu medicine', 'cough syrup purchase',
        'pain killer paracetamol', 'fever medicine dolo', 'headache tablet saridon',
        'band aid first aid', 'antiseptic dettol buy', 'thermometer digital',
        'bp monitor device', 'glucometer strips buy', 'nebulizer mask buy',
        'inhaler asthma refill', 'vaccination shot flu', 'covid test rtpcr',
        'health insurance premium', 'mediclaim policy renewal', 'ambulance charges',
        'surgery hospital bill', 'x ray scan charges', 'mri scan cost',
        'ct scan hospital', 'ultrasound checkup fee', 'ecg test charges',
        'pathology lab tests', 'urine test sample', 'thyroid test charges',
        'diabetes checkup annual', 'cholesterol test lipid', 'liver function test',
        'kidney function test', 'ortho consultation knee', 'spine specialist visit',
        'ent doctor ear nose', 'psychiatrist counseling', 'psychologist therapy',
        'yoga class monthly', 'meditation app subscription', 'sleep aid melatonin',
        'contact lens purchase', 'spectacles new frame', 'lens cleaning solution',
        'sunscreen spf purchase', 'mosquito repellent buy', 'sanitizer hand wash',
        'mask n95 purchase', 'oximeter pulse device', 'hot water bag buy',
    ],
    'Other': [
        'miscellaneous expense', 'donation charity fund', 'gift for friend birthday',
        'laundry dry cleaning', 'passport application fee', 'courier delivery charges',
        'postal stamp letter', 'key duplicate making', 'lock repair service',
        'umbrella repair shop', 'shoe repair cobbler', 'tailor alteration charges',
        'passport photo booth', 'visa application fee', 'pan card application',
        'aadhar card update', 'driving license renewal', 'rcb certificate',
        'notary stamp charge', 'affidavit legal fee', 'court stamp paper',
        'photocopy miscellaneous', 'random impulse buy', 'lost item replacement',
        'fine traffic penalty', 'late fee library', 'penalty charges bank',
        'atm withdrawal fee', 'foreign currency exchange', 'money transfer charges',
        'tips waiter restaurant', 'charity box donation', 'temple offering',
        'church donation', 'mosque offering', 'gurdwara langar donation',
        'pet food purchase', 'dog grooming service', 'vet doctor visit',
        'fish aquarium supplies', 'bird cage seed', 'plant fertilizer buy',
        'garden tools purchase', 'home decor painting', 'wall sticker buy',
    ],
}


def _augment(text: str) -> list[str]:
    """Generate variations of a description for data augmentation."""
    variations = [text]
    words = text.split()

    # Capitalisation variants
    variations.append(text.capitalize())
    variations.append(text.upper())

    # Prefix variants
    prefixes = [
        'paid for ', 'bought ', 'spent on ', 'purchased ', 'payment for ',
        'expense for ', 'charged for ', '', 'monthly ', 'weekly ',
    ]
    for p in random.sample(prefixes, min(3, len(prefixes))):
        variations.append(p + text)

    # Word drop (if long enough)
    if len(words) > 2:
        drop_idx = random.randint(0, len(words) - 1)
        variations.append(' '.join(w for i, w in enumerate(words) if i != drop_idx))

    return variations


def generate_dataset(min_samples: int = 550) -> pd.DataFrame:
    """
    Generate a synthetic expense description dataset with augmentations.
    Guarantees at least `min_samples` rows.
    """
    random.seed(42)
    rows = []

    for category, templates in TEMPLATES.items():
        for tpl in templates:
            augmented = _augment(tpl)
            for desc in augmented:
                rows.append({'description': desc.strip(), 'category': category})

    df = pd.DataFrame(rows).drop_duplicates(subset='description')
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    logger.info("Generated %d samples across %d categories", len(df), df['category'].nunique())
    return df


def train_model(csv_path: str = CSV_PATH, model_path: str = MODEL_PATH):
    """
    Train the category classifier pipeline:
    1. Generate / load dataset
    2. TF-IDF + CalibratedClassifierCV(LinearSVC) via GridSearchCV
    3. Evaluate and persist
    """
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Step 1 – dataset
    if os.path.exists(csv_path):
        logger.info("Loading existing dataset from %s", csv_path)
        df = pd.read_csv(csv_path)
    else:
        df = generate_dataset()
        df.to_csv(csv_path, index=False)
        logger.info("Saved synthetic dataset to %s (%d rows)", csv_path, len(df))

    X = df['description'].astype(str)
    y = df['category'].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    # Step 2 – pipeline (CalibratedClassifierCV wraps LinearSVC to get probabilities)
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(lowercase=True, stop_words='english')),
        ('clf', CalibratedClassifierCV(LinearSVC(max_iter=5000, random_state=42))),
    ])

    param_grid = {
        'tfidf__max_features': [5000, 8000],
        'tfidf__ngram_range': [(1, 1), (1, 2)],
        'tfidf__sublinear_tf': [True, False],
        'clf__estimator__C': [0.5, 1.0, 5.0],
    }

    logger.info("Running GridSearchCV (this may take a minute)...")
    grid = GridSearchCV(
        pipeline, param_grid,
        cv=5, scoring='accuracy', n_jobs=-1, verbose=0,
    )
    grid.fit(X_train, y_train)

    best = grid.best_estimator_
    logger.info("Best params: %s", grid.best_params_)
    logger.info("Best CV accuracy: %.2f%%", grid.best_score_ * 100)

    # Step 3 – evaluate on held-out test set
    y_pred = best.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    logger.info("Test accuracy: %.2f%%", test_acc * 100)
    logger.info("\n%s", classification_report(y_test, y_pred, zero_division=0))

    # Step 4 – persist
    joblib.dump(best, model_path)
    logger.info("Model saved to %s", model_path)

    return best


if __name__ == '__main__':
    train_model()
