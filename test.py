users = {}

person1 = {
    "name": "Alice",
    "age": 25,
    "address": {
        "city": "Toronto",
        "postal": "M1A 2B3"
    }
}

users["person1"] = person1

print(f"Age of {users["person1"]["name"]}: {users["person1"]["age"]}")