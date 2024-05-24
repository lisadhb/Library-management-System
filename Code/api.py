from flask_restful import Resource, Api
from app import app
from models import Section
api=Api(app)

class SectionResource(Resource):
    def get(self):
        sections=Section.query.all()
        return {'sections':[
            {'sec_id':section.sec_id, 
             'sec_name':section.sec_name}
            for section in sections]}
api.add_resource(SectionResource,'/api/section')