import argparse
import collections
import logging
from logging import Logger
from typing import Any
import grpc
from pathlib import Path
from injector import Binder, inject, singleton

from api import api_pb2_grpc as api
from api import api_pb2 as dto
from . import Repository, exc

def bind_usecase(binder: Binder):
	binder.bind(Usecase, Usecase, singleton)

class Usecase:
	@inject
	def __init__(self,
		logger: Logger,
		auth_client: api.AuthStub,
		shop_client: api.ShopStub,
		session_repo: Repository,
	):
		self.log = logger
		self.auth = auth_client
		self.shop = shop_client
		self.repo = session_repo
	
		# TODO login test
		# TODO caching
	def login(self, username: str):
		if self.repo.get_user() is not None:
			raise exc.LoggedInError()
		
		req = dto.LoginReq(username = username)
		resp: dto.UserSession = self.auth.Login(req)

		self.repo.set_token(resp.session_token)

		req = dto.Empty()
		resp: dto.User = self.shop.GetLoginReward(req)

		self.repo.set_user(resp)

	def get_shop_items(self) -> dto.ItemsList:
		shop_items = self.repo.get_shop_items()
		if shop_items is not None:
			return shop_items
		
		req = dto.Empty()
		resp: dto.ItemsList = self.shop.GetShopItems(req)

		self.repo.set_shop_items(resp)
		return resp

	def buy_item(self, item_name: str):
		req = dto.BuyItemReq(item_name = item_name)
		resp: dto.User = self.shop.BuyItem(req)
		self.repo.set_user(resp)

	def sell_item(self, item_name: str):
		req = dto.SellItemReq(item_name = item_name)
		resp: dto.User = self.shop.SellItem(req)
		self.repo.set_user(resp)
	
	def logout(self):
		if self.repo.get_token() is None:
			raise exc.LoggedOutError()
		self.repo.clear()
	
	def get_user(self) -> dto.User:
		user = self.repo.get_user()
		if user is None:
			raise exc.NotLoggedInError()
		
		return user

