# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class RestApi(http.Controller):
    """This is a controller which is used to generate responses based on the
    API requests"""

    def auth_api_key(self, api_key):
        """This function is used to authenticate the API key when sending a
        request"""
        user_id = request.env['res.users'].sudo().search([('api_key', '=', api_key)])
        if api_key is not None and user_id:
            response = True
        elif not user_id:
            response = ('<html><body><h2> Invalid <i>API Key</i> '
                        '!</h2></body></html>')
        else:
            response = ("<html><body><h2>No <i>API Key</i> Provided "
                        "!</h2></body></html>")
        return response

    def generate_response(self, method, model, rec_id, domain=None):
        """This function is used to generate the response based on the type
        of request and the parameters given"""
        option = request.env['connection.api'].sudo().search(
            [('model_id', '=', model)], limit=1)
        model_name = option.model_id.model
        if method != 'DELETE':
            data = json.loads(request.httprequest.data)
        else:
            data = {}

        fields = []
        if data and 'fields' in data:
            fields = data['fields']

        if not fields and method != 'DELETE':
            return ("<html><body><h2>No fields selected for the model"
                    "</h2></body></html>")
        if not option:
            return ("<html><body><h2>No Record Created for the model"
                    "</h2></body></html>")

        try:
            if method == 'GET':
                if not option.is_get:
                    return ("<html><body><h2>Method Not Allowed"
                            "</h2></body></html>")
                else:
                    if rec_id != 0:
                        partner_records = request.env[
                            str(model_name)
                        ].search_read(
                            domain=domain or [('id', '=', rec_id)],
                            fields=fields
                        )
                    else:
                        partner_records = request.env[
                            str(model_name)
                        ].search_read(
                            domain=domain or [],
                            fields=fields
                        )

                    # Manually convert datetime fields to string format
                    for record in partner_records:
                        for key, value in record.items():
                            if isinstance(value, datetime):
                                record[key] = value.isoformat()

                    data = json.dumps({
                        'records': partner_records
                    })
                    return request.make_response(data=data)

            if method == 'POST':
                if not option.is_post:
                    return ("<html><body><h2>Method Not Allowed"
                            "</h2></body></html>")
                else:
                    try:
                        data = json.loads(request.httprequest.data)
                        datas = []
                        new_resource = request.env[str(model_name)].create(
                            data['values'])
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', new_resource.id)],
                            fields=fields
                        )
                        new_data = json.dumps({'New resource': partner_records, })
                        datas.append(new_data)
                        return request.make_response(data=datas)
                    except:
                        return ("<html><body><h2>Invalid JSON Data"
                                "</h2></body></html>")

            if method == 'PUT':
                if not option.is_put:
                    return ("<html><body><h2>Method Not Allowed"
                            "</h2></body></html>")
                else:
                    if rec_id == 0:
                        return ("<html><body><h2>No ID Provided"
                                "</h2></body></html>")
                    else:
                        resource = request.env[str(model_name)].browse(
                            int(rec_id))
                        if not resource.exists():
                            return ("<html><body><h2>Resource not found"
                                    "</h2></body></html>")
                        else:
                            try:
                                datas = []
                                data = json.loads(request.httprequest.data)
                                resource.write(data['values'])
                                partner_records = request.env[
                                    str(model_name)].search_read(
                                    domain=[('id', '=', resource.id)],
                                    fields=fields
                                )
                                new_data = json.dumps(
                                    {'Updated resource': partner_records,
                                     })
                                datas.append(new_data)
                                return request.make_response(data=datas)

                            except:
                                return ("<html><body><h2>Invalid JSON Data "
                                        "!</h2></body></html>")

            if method == 'DELETE':
                if not option.is_delete:
                    return ("<html><body><h2>Method Not Allowed"
                            "</h2></body></html>")
                else:
                    if rec_id == 0:
                        return ("<html><body><h2>No ID Provided"
                                "</h2></body></html>")
                    else:
                        resource = request.env[str(model_name)].browse(
                            int(rec_id))
                        if not resource.exists():
                            return ("<html><body><h2>Resource not found"
                                    "</h2></body></html>")
                        else:
                            records = request.env[
                                str(model_name)].search_read(
                                domain=[('id', '=', resource.id)],
                                fields=['id', 'display_name']
                            )
                            remove = json.dumps(
                                {"Resource deleted": records,
                                 })
                            resource.unlink()
                            return request.make_response(data=remove)

        except Exception as e:
            _logger.error("Error in generate_response: %s", e)
            return ("<html><body><h2>Invalid JSON Data"
                    "</h2></body></html>")

    @http.route(['/send_request'], type='http',
                auth='none',
                methods=['GET', 'POST', 'PUT', 'DELETE'], csrf=False)
    def fetch_data(self, **kw):
        """This controller will be called when sending a request to the
        specified URL, and it will authenticate the API key and then will
        generate the result"""

        http_method = request.httprequest.method
        api_key = request.httprequest.headers.get('api-key')
        auth_api = self.auth_api_key(api_key)
        model = kw.get('model')
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        request.session.authenticate(request.session.db, username,
                                     password)
        model_id = request.env['ir.model'].sudo().search(
            [('model', '=', model)])
        if not model_id:
            return ("<html><body><h3>Invalid model, check spelling or maybe "
                    "the related "
                    "module is not installed"
                    "</h3></body></html>")

        if auth_api == True:
            rec_id = int(kw.get('Id', 0))
            domain = kw.get('domain', [])
            result = self.generate_response(http_method, model_id.id, rec_id, domain)
            return result
        else:
            return auth_api

    @http.route(['/odoo_connect'], type="http", auth="none", csrf=False,
                methods=['GET'])
    def odoo_connect(self, **kw):
        """This is the controller which initializes the API transaction by
        generating the API key for specific user and database"""

        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        db = request.httprequest.headers.get('db')
        try:
            request.session.update(http.get_default_session(), db=db)
            auth = request.session.authenticate(request.session.db, username,
                                                password)
            user = request.env['res.users'].browse(auth)
            api_key = request.env.user.generate_api(username)
            datas = json.dumps({"Status": "auth successful",
                                "User": user.name,
                                "UserId": user.id,
                                "api-key": api_key})
            return request.make_response(data=datas)
        except:
            return ("<html><body><h2>wrong login credentials"
                    "</h2></body></html>")

    @http.route('/api/button_action', type='http', auth="public", csrf=False)
    def button_action(self, **kw):
        order_id = request.env[kw.get('model_name')].sudo().browse(int(kw.get('id')))
        button_action = getattr(order_id, kw.get('button_name'), None)
        if button_action:
            button_action()
        return request.make_response("<html><body><h2>Button action executed!</h2></body></html>")

    @http.route('/api/search_domain', type='json', auth='public', methods=['POST'], csrf=False)
    def get_data(self, **kw):
        # Decode and parse the raw request data
        data = json.loads(request.httprequest.data.decode('utf-8'))

        # Extract model_name and domain
        model_name = data.get('model_name')
        domain = data.get('domain', [])

        print("Model Name:", model_name)
        print("Domain:", domain)

        try:
            # Get model dynamically using model name
            Model = request.env[model_name]

            # Apply the domain filter
            records = Model.sudo().search(domain)
            print(records)
            # Prepare the result by looping through each record
            result = []
            for record in records:
                print(record)
                # Read data for each record individually
                record_data = record.read()[0]
                result.append(record_data)

            return {'status': 'success', 'data': result}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/get_chatter', type='json', auth='public', methods=['POST'], csrf=False)
    def get_chatter(self, **kw):
        # Decode and parse the raw request data
        data = json.loads(request.httprequest.data.decode('utf-8'))

        # Extract model_name and record_id from the request
        model_name = data.get('model_name')
        record_id = data.get('record_id')

        print("Model Name:", model_name)
        print("Record ID:", record_id)

        try:
            # Get the model dynamically using the model name
            Model = request.env[model_name]

            # Fetch the record
            record = Model.sudo().browse(record_id)

            if not record.exists():
                return {'status': 'error', 'message': 'Record not found'}

            # Get chatter messages
            chatter_messages = record.message_ids

            # Prepare the result
            result = []
            for message in chatter_messages:
                message_data = {
                    'id': message.id,
                    'author_id': message.author_id.id,
                    'author_name': message.author_id.name,
                    'date': message.date,
                    'body': message.body,
                }
                result.append(message_data)

            return {'status': 'success', 'data': result}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/add_message', type='json', auth='public', methods=['POST'], csrf=False)
    def add_message(self, **kw):
        # Decode and parse the raw request data
        data = json.loads(request.httprequest.data.decode('utf-8'))

        # Extract model_name, record_id, message, and author_id from the request
        model_name = data.get('model_name')
        record_id = data.get('record_id')
        message_body = data.get('message')
        author_id = data.get('author_id')

        print("Model Name:", model_name)
        print("Record ID:", record_id)
        print("Message:", message_body)
        print("Author ID:", author_id)

        try:
            # Get the model dynamically using the model name
            Model = request.env[model_name]

            # Fetch the record
            record = Model.sudo().browse(record_id)

            if not record.exists():
                return {'status': 'error', 'message': 'Record not found'}

            # Post the message to the chatter with the specified author
            record.message_post(body=message_body, author_id=author_id)

            return {'status': 'success', 'message': 'Message added successfully'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/create_activity', type='json', auth='public', methods=['POST'], csrf=False)
    def create_activity(self, **kw):
        # Decode and parse the raw request data
        data = json.loads(request.httprequest.data.decode('utf-8'))

        # Extract model_name, record_id, activity_type, summary, and user_id from the request
        model_name = data.get('model_name')
        record_id = data.get('record_id')
        activity_type = data.get('activity_type')  # e.g., 'meeting'
        summary = data.get('summary')  # Brief description of the activity
        user_id = data.get('user_id')  # The ID of the user assigned to the activity

        print("Model Name:", model_name)
        print("Record ID:", record_id)
        print("Activity Type:", activity_type)
        print("Summary:", summary)
        print("User ID:", user_id)

        try:
            # Get the model dynamically using the model name
            Model = request.env[model_name]

            # Fetch the record
            record = Model.sudo().browse(record_id)

            if not record.exists():
                return {'status': 'error', 'message': 'Record not found'}

            # Fetch the activity type by name
            activity_type_record = request.env['mail.activity.type'].sudo().search([('name', '=', activity_type)],
                                                                                   limit=1)

            if not activity_type_record:
                return {'status': 'error', 'message': 'Activity type not found'}

            # Create the activity
            activity_vals = {
                'res_id': record.id,
                'res_model': model_name,
                'activity_type_id': activity_type_record.id,
                'summary': summary,
                'user_id': user_id,
            }

            request.env['mail.activity'].sudo().create(activity_vals)

            return {'status': 'success', 'message': 'Activity created successfully'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/user/signup', type='http', auth='public', methods=['POST'], csrf=False)
    def create_users_sign_up(self, **kwargs):
        """
        Create a user and assign it to the portal group.

        Accepts HTTP POST requests with parameters:
        - name: str, required
        - email: str, required
        - password: str, required
        - phone: str, optional
        """
        name = kwargs.get('name')
        email = kwargs.get('email')
        password = kwargs.get('password')
        phone = kwargs.get('phone', '')

        # Validate required fields
        if not all([name, email, password]):
            return request.make_response(
                json.dumps({
                    "error": "Missing required fields: name, email, and password are mandatory."
                }),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        try:
            # Create a partner
            partner_id = request.env['res.partner'].sudo().create({
                'name': name,
                'email': email,
                'phone': phone
            })

            # Retrieve portal group reference
            group_portal = request.env.ref('base.group_portal')

            # Create a user linked to the partner and assign to portal group
            user = request.env['res.users'].sudo().create({
                'name': partner_id.name,
                'login': partner_id.email,
                'partner_id': partner_id.id,
                'password': password,
                'groups_id': [(4, group_portal.id)]
            })

            # Return success response
            response_data = {
                'success': True,
                'partner_name': partner_id.name,
                'partner_email': partner_id.email,
                'user_name': user.name,
                'user_id': user.id
            }

            return request.make_response(
                json.dumps(response_data),
                headers={'Content-Type': 'application/json'}
            )

        except Exception as e:
            return request.make_response(
                json.dumps({
                    "error": "An error occurred while creating the user.",
                    "details": str(e)
                }),
                headers={'Content-Type': 'application/json'},
                status=500
            )

    @http.route('/get_agents', auth='public', type='http', methods=['GET'], csrf=False)
    def get_agents(self):
        # Fetch all partners
        partners = request.env['res.partner'].sudo().search([('is_agent', '=', True)])
        # Prepare the response data
        agent_data = []
        for partner in partners:
            agent_data.append({
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'is_agent': partner.is_agent,
            })

        # Return the agent data as a JSON response
        return request.make_response(json.dumps(agent_data), headers={'Content-Type': 'application/json'})

        # # Return the data as a JSON response
        # return agent_data

    @http.route('/get_branch_approvals/<int:create_uid>', auth='public', type='http', methods=['GET'], csrf=False)
    def get_approvals(self, create_uid):
        # Build the domain for the search
        domain = [('create_uid', '=', create_uid)]

        # Fetch the approvals based on the domain (with or without create_uid filter)
        approvals = request.env['branch.approval'].sudo().search(domain)

        # Prepare the response data
        approval_data = []

        # Loop through each approval record
        for approval in approvals:
            # Get all fields for the approval record using the `read()` method
            fields = approval.read()

            # Convert datetime fields to string format
            for field_name, value in fields[0].items():
                if isinstance(value, datetime):
                    fields[0][field_name] = value.strftime('%Y-%m-%d %H:%M:%S')  # You can adjust the format as needed

            # Add the processed fields to the response data
            approval_data.append(
                fields[0])  # `fields[0]` is the dictionary containing all field values for the current record

        # Return the approval data as a JSON response
        return request.make_response(json.dumps(approval_data), headers={'Content-Type': 'application/json'})

    @http.route('/get_countries', type='http', auth="public", methods=['GET'], csrf=False)
    def get_all_countries(self):
        # Fetch all countries from the res.country model
        countries = request.env['res.country'].sudo().search([])  # Empty search domain fetches all records

        # Prepare a list to hold country data
        country_data = []
        for country in countries:
            country_data.append({
                'id': country.id,
                'name': country.name,
                'code': country.code,
            })

        # Return the JSON response using request.make_response
        return request.make_response(
            json.dumps(country_data),
            headers={'Content-Type': 'application/json'}
        )

    @http.route(['/user/read'], type="http", auth="public", csrf=False)
    def search_users(self, login=None, **kwargs):
        try:
            users = request.env['res.users'].sudo().search([('login', '=', str(login))])
            return Response(
                content_type='application/json',
                response=http.json.dumps({"status": "success", "users": users.id}),
                status=200
            )
        except Exception as e:
            return Response(
                content_type='application/json',
                response=http.json.dumps({"status": "error", "message": str(e)}),
                status=500
            )

    @http.route('/get_access_token', auth='public', type='http', methods=['GET'], csrf=False)
    def get_token(self, invoice_id):
        try:
            invoice_id = int(invoice_id)
            move = request.env['account.move'].sudo().browse(invoice_id)
            if not move.exists() or move.move_type != 'out_invoice':
                return request.not_found()
            token = move._portal_ensure_token()
            return f"/my/invoices/{int(invoice_id)}?access_token={token}"
        except (ValueError, TypeError):
            return request.not_found()
