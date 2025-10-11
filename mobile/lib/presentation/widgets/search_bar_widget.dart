import 'package:flutter/material.dart';
import 'accessibility_text_field.dart';
import 'accessibility_button.dart';

class SearchBarWidget extends StatefulWidget {
  final void Function(String query) onSearch;

  const SearchBarWidget({
    super.key,
    required this.onSearch,
  });

  @override
  State<SearchBarWidget> createState() => _SearchBarWidgetState();
}

class _SearchBarWidgetState extends State<SearchBarWidget> {
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    // 다이얼로그가 열리면 자동으로 포커스
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _focusNode.requestFocus();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('도서 검색'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          AccessibilityTextField(
            controller: _searchController,
            labelText: '검색어',
            hintText: '제목, 저자 또는 키워드를 입력하세요',
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _performSearch(),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('취소'),
              ),
              const SizedBox(width: 8),
              AccessibilityButton(
                onPressed: _performSearch,
                text: '검색',
                width: 100,
                height: 45,
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _performSearch() {
    final query = _searchController.text.trim();
    if (query.isNotEmpty) {
      widget.onSearch(query);
    }
  }
}