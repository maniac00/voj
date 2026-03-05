import 'package:flutter/material.dart';

/// 화면 진입/복귀 이벤트 감지를 위한 전역 RouteObserver
final RouteObserver<ModalRoute<dynamic>> appRouteObserver =
    RouteObserver<ModalRoute<dynamic>>();
