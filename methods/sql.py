import sqlalchemy as sq


class Sql_db:
    def __init__(self):
        self.engine = sq.create_engine('sqlite:///database.db')
        self.connection = self.engine.connect()

        self.metadata = sq.MetaData()

        self.users = sq.Table("users", self.metadata,
                              sq.Column("user_id", sq.Integer, primary_key=True),
                              sq.Column("chat_id", sq.Integer),
                              sq.Column("username_tg", sq.Text),
                              sq.Column("first_name", sq.Text),
                              sq.Column("sub_status", sq.Integer, default=3),
                              sq.Column("openAI_token", sq.Text, default="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")
                              )

        self.metadata.create_all(self.engine)

    def add_user(self, chat_id, username_tg, first_name):
        insertion_query = self.users.insert().values([
            {"chat_id": chat_id, "username_tg": username_tg, "first_name": first_name}
        ])

        self.connection.execute(insertion_query)

    def find_user(self, chat_id):
        data = sq.select(self.users).where(self.users.columns.chat_id == chat_id)
        data_result = self.connection.execute(data)
        return data_result.fetchall()[0]

    def change_token(self, chat_id, token):
        update = sq.update(self.users).where(self.users.columns.chat_id == chat_id).values(openAI_token = token)
        self.connection.execute(update)