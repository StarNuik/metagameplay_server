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
from . import Repository

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
	
	def login(self, username: str) -> dto.User:
		# TODO login test
		# TODO caching
		req = dto.LoginReq(username = username)
		
		resp: dto.UserSession = self.auth.Login(req)

		self.repo.set_token(resp.session_token)

		resp = self.shop.GetLoginReward(dto.Empty())
		return resp

	def logout(self):
		self.repo.clear()

	def get_shop_items(self) -> dto.ItemsList:
		resp = self.shop.GetShopItems(dto.Empty())
		return resp

	def buy_item(self, item_name: str) -> dto.User:
		req = dto.BuyItemReq(item_name = item_name)
		resp: dto.User = self.shop.BuyItem(req)
		return resp

	def sell_item(self, item_name: str) -> dto.User:
		req = dto.SellItemReq(item_name = item_name)
		resp: dto.User = self.shop.SellItem(req)
		return resp
