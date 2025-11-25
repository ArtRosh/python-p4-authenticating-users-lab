#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)


# ---------- вспомогательный сброс сессии (clear) ----------

class ClearSession(Resource):
    def delete(self):
        session['page_views'] = None
        session['user_id'] = None
        return '', 204


# ---------- статьи (из предыдущего задания) ----------

class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return articles, 200


class ShowArticle(Resource):
    def get(self, id):
        # инициализируем/увеличиваем счётчик просмотров
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:
            article = Article.query.filter(Article.id == id).first()
            if not article:
                return {'message': 'Article not found'}, 404

            article_json = jsonify(article.to_dict())
            return make_response(article_json, 200)

        return {'message': 'Maximum pageview limit reached'}, 401


# ---------- аутентификация / сессии ----------

class Login(Resource):
    def post(self):
        # берём username из JSON
        data = request.get_json()
        username = data.get('username') if data else None

        if not username:
            return {'message': 'Username required'}, 400

        # ищем пользователя по username
        user = User.query.filter(User.username == username).first()
        if not user:
            return {'message': 'User not found'}, 404

        # сохраняем user_id в сессии
        session['user_id'] = user.id

        # отдаём пользователя как JSON
        return user.to_dict(), 200


class Logout(Resource):
    def delete(self):
        # удаляем user_id из сессии
        session['user_id'] = None
        return '', 204


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if not user_id:
            # нет user_id в сессии → не авторизован
            return {}, 401

        user = User.query.filter(User.id == user_id).first()
        if not user:
            # на всякий случай, если user удалён
            return {}, 401

        # есть user_id и пользователь найден → вернуть JSON
        return user.to_dict(), 200


# ---------- ресурсы / маршруты ----------

api.add_resource(ClearSession, '/clear')

api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')

api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')


if __name__ == '__main__':
    app.run(port=5555, debug=True)