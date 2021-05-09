# DBS 2021

Azure website: https://fiit-dbs-xpidanic-app.azurewebsites.net/

## Run application
- in settings.py in section DATABASES comment whole azure production part and uncomment development part
- in project root create file secrets.json:
```
    {
        "DB_PASSWORD": "",
        "DB_NAME": "",
        "DB_HOST": "",
        "DB_USER": "",
    }
```
- run commands: 
```
    pip install -r requirements.txt
    python3 manage.py runserver
```

## Task 1 - Uptime
- url: 
```
    /v1/health/
```

- response: 
``` 
    {
        "pgsql": {
            "uptime": "15 days, 18:14:13"
        }
    }
```

## Task 2 - Submissions
### GET
- url:
```
    /v1/ov/submissions/
```

- query_params:
```
    page - default 1,
    per_page - default 10,
    query - default "",
    registration_date_lte - default "1000-01-01",
    registration_date_gte - default "3000-01-01",
    order_by - default id,
    order_type - default DESC
```

- response:
```
    {
        "result": [
            {
                "metadata": {
                    "page": num,
                    "per_page": num,
                    "pages": num,
                    "total": num
                }
            },
            {
                "items": [
                    ...
                ]
            }
        ]
    }   
```

### POST
- url:
```
    /v1/ov/submissions/
```

- body:
```
    br_court_name – required
    kind_name – required
    cin – required, must be number
    registration_date – required, date only from actual year
    corporate_body_name – required
    br_section – required
    br_insertion – required
    street – required
    postal_code – required
    city – required
```

- response:
```
    Status: 201 Created

    {
        "created_submission": [
            {
                ...
            }
        ]
    }
```

- error response:
```
    Status: 422 Unprocessable entity

    {
        "errors": [
            {
                "field": "",
                "reasons": ""
            },
            ...
        ]
    }
```

### DELETE
- url:
```
    /v1/ov/submissions/<id>
```

- response:
```
    Status: 204 No content
```

- error response:
```
    Status: 404 Not found
```

## Task 3 - Companies
### GET
- url:
```
    /v1/companies/
```

- query_params:
```
    page - default 1,
    per_page - default 10,
    query - default "",
    last_update_lte - default "1000-01-01",
    last_update_gte - default "3000-01-01",
    order_by - default cin,
    order_type - default DESC
```

- response:
```
    Status: 200 OK

    {
        "result": [
            {
                "metadata": {
                    "page": num,
                    "per_page": num,
                    "pages": num,
                    "total": num
                }
            },
            {
                "items": [
                    {
                        "cin": num,
                        "name": "",
                        "br_section": "",
                        "address_line": "",
                        "last_update": "",
                        "or_podanie_issues_count": num,
                        "znizenie_imania_issues_count": num,
                        "likvidator_issues_count": num,
                        "konkurz_vyrovnanie_issues_count": num,
                        "konkurz_restrukturalizacia_actors_count": num
                    },
                    ...
                ]
            }
        ]
    }   
```

## Task 5 - ORM
### submissions GET
- url:
```
    /v2/ov/submissions/
```

- query_params:
```
    page - default 1,
    per_page - default 10,
    query - default "",
    registration_date_lte - default "1000-01-01",
    registration_date_gte - default "3000-01-01",
    order_by - default id,
    order_type - default DESC
```

- response:
```
    {
        "result": [
            {
                "metadata": {
                    "page": num,
                    "per_page": num,
                    "pages": num,
                    "total": num
                }
            },
            {
                "items": [
                    ...
                ]
            }
        ]
    }   
```

### submissions single GET
- url:
```
    /v2/ov/submissions/<id>
```

- response:
```
    {
        "response": {
            "id": int,
            "br_court_name": "",
            "kind_name": "",
            "cin": int,
            "registration_date": date,
            "corporate_body_name": "",
            "br_section": "",
            "br_insertion": "",
            "text": "",
            "street": "",
            "postal_code": "",
            "city": ""
        }
    }   
```

- error response:
```
    Status: 404 Not found

    {
        "error": {
            "message": "Záznam neexistuje"
        }
    }
```

### submissions POST
- url:
```
    /v2/ov/submissions/
```

- body:
```
    br_court_name – required
    kind_name – required
    cin – required, must be number
    registration_date – required, date only from actual year
    corporate_body_name – required
    br_section – required
    br_insertion – required
    street – required
    postal_code – required
    city – required
```

- response:
```
    Status: 201 Created

    {
        "created_submission": [
            {
                ...
            }
        ]
    }
```

- error response:
```
    Status: 422 Unprocessable entity

    {
        "errors": [
            {
                "field": "",
                "reasons": ""
            },
            ...
        ]
    }
```

### submissions DELETE
- url:
```
    /v2/ov/submissions/<id>
```

- response:
```
    Status: 204 No content
```

- error response:
```
    Status: 404 Not found

    {
        "error": {
            "message": "Záznam neexistuje"
        }
    }
```

### submissions PUT
- url:
```
    /v2/ov/submissions/<id>
```

- body:
```
    br_court_name
    kind_name
    cin - must be number
    registration_date – date only from actual year
    corporate_body_name
    br_section
    br_insertion
    street
    postal_code
    city
```

- response:
```
    Status: 201 Created

    {
        "response": [
            {
                ...
            }
        ]
    }
```

- error responses:
```
    Status: 422 Unprocessable entity

    {
        "errors": [
            {
                "field": "",
                "reasons": ""
            },
            ...
        ]
    }

    Status: 404 Not found

    {
        "error": {
            "message": "Záznam neexistuje"
        }
    }
```

### companies GET
- url:
```
    /v2/companies/
```

- query_params:
```
    page - default 1,
    per_page - default 10,
    query - default "",
    last_update_lte - default "1000-01-01",
    last_update_gte - default "3000-01-01",
    order_by - default cin,
    order_type - default DESC
```

- response:
```
    Status: 200 OK

    {
        "result": [
            {
                "metadata": {
                    "page": num,
                    "per_page": num,
                    "pages": num,
                    "total": num
                }
            },
            {
                "items": [
                    {
                        "cin": num,
                        "name": "",
                        "br_section": "",
                        "address_line": "",
                        "last_update": "",
                        "or_podanie_issues_count": num,
                        "znizenie_imania_issues_count": num,
                        "likvidator_issues_count": num,
                        "konkurz_vyrovnanie_issues_count": num,
                        "konkurz_restrukturalizacia_actors_count": num
                    },
                    ...
                ]
            }
        ]
    }   
```