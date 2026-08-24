import urllib.request
import json

def test_api(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        body = json.dumps(data).encode('utf-8')
    else:
        body = None
    with urllib.request.urlopen(req, data=body) as res:
        return json.loads(res.read().decode('utf-8'))

try:
    print('--- TESTING PUC DIGITAL BOOKSTORE CUSTOMER REST API ---')
    depts = test_api('http://localhost:8000/api/departments/')
    print('1. Departments:', depts)

    books = test_api('http://localhost:8000/api/books/')
    print(f'2. Books Count: {len(books)}')
    if books:
        print(f'   First Book: {books[0]["title"]} (${books[0]["price"]}, Stock: {books[0]["stock_quantity"]})')

    login_res = test_api('http://localhost:8000/api/login/', 'POST', {
        'email': 'dara.sok@student.puc.edu.kh',
        'password': 'student123'
    })
    print('3. Student Login:', login_res)

    user_id = login_res['user']['user_id']
    order_res = test_api('http://localhost:8000/api/orders/', 'POST', {
        'user_id': user_id,
        'total_amount': 36.50,
        'payment_method': 'Stripe Card',
        'stripe_payment_id': 'ST-TEST-1001',
        'items': [{
            'book_id': books[0]['book_id'],
            'quantity': 2,
            'unit_price': books[0]['price']
        }]
    })
    print('4. Create Order with PIN:', order_res)

    user_orders = test_api(f'http://localhost:8000/api/orders/{user_id}')
    print(f'5. User Orders Count: {len(user_orders)}')
    print('   Latest Order:', user_orders[0])

    order_id = order_res['order_id']
    detail = test_api(f'http://localhost:8000/api/orders/detail/{order_id}')
    print('6. Order Line Items:', detail)

    cancel_res = test_api(f'http://localhost:8000/api/orders/{order_id}/cancel/', 'PATCH')
    print('7. Cancel Order & Restore Stock:', cancel_res)

    print('\n[SUCCESS] ALL CUSTOMER REST API ENDPOINTS ARE FULLY OPERATIONAL!')
except Exception as e:
    print(f'[ERROR] API Test Failed: {e}')
