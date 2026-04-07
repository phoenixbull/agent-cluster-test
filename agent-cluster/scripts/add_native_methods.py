#!/usr/bin/env python3
"""
脚本：向 agent_executor.py 添加 Native 移动端代码生成方法
保持正确缩进（类方法缩进 4 空格）
"""

native_methods = '''
    # ========== P1 新增：Native 移动端代码生成方法 ==========
    
    def _generate_ios_code(self, task: str) -> Dict:
        """生成 iOS 代码 (Swift/SwiftUI)"""
        task_lower = task.lower()
        
        if "登录" in task or "login" in task_lower:
            return {
                "files": [
                    {
                        "filename": "LoginView.swift",
                        "language": "swift",
                        "content": self._get_ios_login_view_code()
                    },
                    {
                        "filename": "AuthService.swift",
                        "language": "swift",
                        "content": self._get_ios_auth_service_code()
                    }
                ]
            }
        elif "列表" in task or "list" in task_lower or "todo" in task_lower:
            return {
                "files": [
                    {
                        "filename": "ContentView.swift",
                        "language": "swift",
                        "content": self._get_ios_list_view_code()
                    }
                ]
            }
        else:
            return {
                "files": [
                    {
                        "filename": "ContentView.swift",
                        "language": "swift",
                        "content": self._get_ios_generic_view_code(task)
                    }
                ]
            }
    
    def _generate_android_code(self, task: str) -> Dict:
        """生成 Android 代码 (Kotlin/Jetpack Compose)"""
        task_lower = task.lower()
        
        if "登录" in task or "login" in task_lower:
            return {
                "files": [
                    {
                        "filename": "LoginScreen.kt",
                        "language": "kotlin",
                        "content": self._get_android_login_screen_code()
                    },
                    {
                        "filename": "AuthRepository.kt",
                        "language": "kotlin",
                        "content": self._get_android_auth_repository_code()
                    }
                ]
            }
        else:
            return {
                "files": [
                    {
                        "filename": "MainActivity.kt",
                        "language": "kotlin",
                        "content": self._get_android_generic_screen_code(task)
                    }
                ]
            }
    
    def _generate_react_native_code(self, task: str) -> Dict:
        """生成 React Native 代码"""
        return {
            "files": [
                {
                    "filename": "App.tsx",
                    "language": "typescript",
                    "content": self._get_react_native_app_code(task)
                },
                {
                    "filename": "package.json",
                    "language": "json",
                    "content": self._get_react_native_package_json()
                }
            ]
        }
    
    def _generate_flutter_code(self, task: str) -> Dict:
        """生成 Flutter 代码"""
        return {
            "files": [
                {
                    "filename": "main.dart",
                    "language": "dart",
                    "content": self._get_flutter_main_code(task)
                },
                {
                    "filename": "pubspec.yaml",
                    "language": "yaml",
                    "content": self._get_flutter_pubspec()
                }
            ]
        }
    
    def _generate_mobile_test_assets(self, task: str) -> Dict:
        """生成移动端测试代码"""
        return {
            "files": [
                {
                    "filename": "AppTests.swift",
                    "language": "swift",
                    "content": self._get_ios_test_code()
                },
                {
                    "filename": "AppInstrumentedTests.kt",
                    "language": "kotlin",
                    "content": self._get_android_test_code()
                }
            ]
        }
    
    # ========== iOS 代码模板 ==========
    
    def _get_ios_login_view_code(self) -> str:
        return \'\'\'import SwiftUI

struct LoginView: View {
    @StateObject private var viewModel = LoginViewModel()
    @State private var username = ""
    @State private var password = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("账户信息")) {
                    TextField("用户名", text: $username)
                        .autocapitalization(.none)
                    SecureField("密码", text: $password)
                }
                
                Section {
                    Button(action: {
                        viewModel.login(username: username, password: password)
                    }) {
                        HStack {
                            Spacer()
                            Text("登录")
                                .fontWeight(.semibold)
                            Spacer()
                        }
                    }
                    .disabled(username.isEmpty || password.isEmpty)
                }
            }
            .navigationTitle("登录")
            .alert(item: $viewModel.errorMessage) { error in
                Alert(title: Text("登录失败"), message: Text(error))
            }
        }
    }
}

class LoginViewModel: ObservableObject {
    @Published var errorMessage: String?
    
    func login(username: String, password: String) {
        guard !username.isEmpty, !password.isEmpty else {
            errorMessage = "用户名和密码不能为空"
            return
        }
    }
}

#Preview {
    LoginView()
}
\'\'\'

    def _get_ios_auth_service_code(self) -> str:
        return \'\'\'import Foundation

class AuthService {
    static let shared = AuthService()
    private let session: URLSession
    
    init() {
        let config = URLSessionConfiguration.default
        self.session = URLSession(configuration: config)
    }
    
    func login(username: String, password: String, completion: @escaping (Result<User, Error>) -> Void) {
        guard let url = URL(string: "https://api.example.com/auth/login") else {
            completion(.failure(AuthError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: String] = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        let task = session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            guard let data = data else {
                completion(.failure(AuthError.noData))
                return
            }
            do {
                let decoder = JSONDecoder()
                let user = try decoder.decode(User.self, from: data)
                completion(.success(user))
            } catch {
                completion(.failure(error))
            }
        }
        task.resume()
    }
}

enum AuthError: LocalizedError {
    case invalidURL, noData, invalidResponse
    var errorDescription: String? {
        switch self {
        case .invalidURL: return "无效的 URL"
        case .noData: return "没有收到数据"
        case .invalidResponse: return "响应无效"
        }
    }
}

struct User: Codable {
    let id: String
    let username: String
    let email: String
}
\'\'\'

    def _get_ios_list_view_code(self) -> str:
        return \'\'\'import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = TodoViewModel()
    
    var body: some View {
        NavigationView {
            List(viewModel.items) { item in
                HStack {
                    Image(systemName: item.completed ? "checkmark.circle.fill" : "circle")
                        .foregroundColor(item.completed ? .green : .gray)
                    Text(item.title).strikethrough(item.completed)
                    Spacer()
                }
                .onTapGesture {
                    withAnimation { viewModel.toggle(item) }
                }
            }
            .navigationTitle("待办事项")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: viewModel.addNew) { Image(systemName: "plus") }
                }
            }
        }
    }
}

class TodoViewModel: ObservableObject {
    @Published var items: [TodoItem] = []
    init() { loadItems() }
    func loadItems() {
        items = [
            TodoItem(id: UUID(), title: "学习 Swift", completed: false),
            TodoItem(id: UUID(), title: "开发 iOS 应用", completed: false)
        ]
    }
    func toggle(_ item: TodoItem) {
        if let index = items.firstIndex(where: { $0.id == item.id }) {
            items[index].completed.toggle()
        }
    }
    func addNew() { items.append(TodoItem(id: UUID(), title: "新任务", completed: false)) }
}

struct TodoItem: Identifiable, Codable {
    let id: UUID
    var title: String
    var completed: Bool
}

#Preview { ContentView() }
\'\'\'

    def _get_ios_generic_view_code(self, task: str) -> str:
        return f\'\'\'import SwiftUI

struct ContentView: View {{
    var body: some View {{
        VStack {{
            Image(systemName: "swift")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("{task}").padding()
        }}
        .padding()
    }}
}}

#Preview {{ ContentView() }}
\'\'\'

    # ========== Android 代码模板 ==========
    
    def _get_android_login_screen_code(self) -> str:
        return \'\'\'package com.example.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun LoginScreen(
    viewModel: LoginViewModel = viewModel(),
    onLoginSuccess: () -> Unit
) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(text = "用户登录", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(32.dp))
        OutlinedTextField(value = username, onValueChange = { username = it },
            label = { Text("用户名") }, modifier = Modifier.fillMaxWidth())
        Spacer(modifier = Modifier.height(16.dp))
        OutlinedTextField(value = password, onValueChange = { password = it },
            label = { Text("密码") }, modifier = Modifier.fillMaxWidth())
        Spacer(modifier = Modifier.height(24.dp))
        Button(onClick = { viewModel.login(username, password) },
            modifier = Modifier.fillMaxWidth(),
            enabled = username.isNotEmpty() && password.isNotEmpty()) {
            Text("登录")
        }
    }
}
\'\'\'

    def _get_android_auth_repository_code(self) -> str:
        return \'\'\'package com.example.app.data

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApi {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse
}

data class LoginRequest(val username: String, val password: String)
data class LoginResponse(val token: String, val user: User)
data class User(val id: String, val username: String, val email: String)

class AuthRepository(private val authApi: AuthApi) {
    fun login(username: String, password: String): Flow<Result<String>> = flow {
        try {
            val response = authApi.login(LoginRequest(username, password))
            emit(Result.success(response.token))
        } catch (e: Exception) {
            emit(Result.failure(e))
        }
    }
}
\'\'\'

    def _get_android_generic_screen_code(self, task: str) -> str:
        return f\'\'\'package com.example.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun MainActivity() {{
    Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {{
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {{
            Text(text = "{task}")
        }}
    }}
}}
\'\'\'

    # ========== React Native 代码模板 ==========
    
    def _get_react_native_app_code(self, task: str) -> str:
        return f\'\'\'import React, {{ useState }} from 'react';
import {{ StyleSheet, Text, View, TextInput, Button, SafeAreaView }} from 'react-native';

export default function App() {{
  const [value, setValue] = useState('');
  return (
    <SafeAreaView style={{styles.container}}>
      <View style={{styles.content}}>
        <Text style={{styles.title}}>{task}</Text>
        <TextInput style={{styles.input}} value={{value}} onChangeText={{setValue}} placeholder="输入" />
        <Button title="提交" onPress={{() => console.log(value)}} />
      </View>
    </SafeAreaView>
  );
}}

const styles = StyleSheet.create({{
  container: {{ flex: 1, backgroundColor: '#f5f5f5' }},
  content: {{ flex: 1, padding: 20, justifyContent: 'center' }},
  title: {{ fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' }},
  input: {{ backgroundColor: 'white', padding: 15, borderRadius: 8, marginBottom: 20 }},
}});
\'\'\'

    def _get_react_native_package_json(self) -> str:
        return \'\'\'{
  "name": "react-native-app",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "start": "react-native start",
    "test": "jest"
  },
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.73.0"
  }
}
\'\'\'

    # ========== Flutter 代码模板 ==========
    
    def _get_flutter_main_code(self, task: str) -> str:
        return f\'\'\'import 'package:flutter/material.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});
  @override
  Widget build(BuildContext context) {{
    return MaterialApp(title: 'Flutter App', home: const MyHomePage());
  }}
}}

class MyHomePage extends StatefulWidget {{
  const MyHomePage({{super.key}});
  @override
  State<MyHomePage> createState() => _MyHomePageState();
}}

class _MyHomePageState extends State<MyHomePage> {{
  int _counter = 0;
  void _incrementCounter() => setState(() => _counter++);

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(title: Text('{task}')),
      body: Center(child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [const Text('点击次数:'), Text('$_counter', style: Theme.of(context).textTheme.headlineMedium)]
      )),
      floatingActionButton: FloatingActionButton(onPressed: _incrementCounter, child: const Icon(Icons.add)),
    );
  }}
}}
\'\'\'

    def _get_flutter_pubspec(self) -> str:
        return \'\'\'name: flutter_app
description: A new Flutter project.
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.2.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  provider: ^6.1.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
\'\'\'

    # ========== 移动端测试代码模板 ==========
    
    def _get_ios_test_code(self) -> str:
        return \'\'\'import XCTest

final class AppTests: XCTestCase {
    func testLoginSuccess() throws {
        let viewModel = LoginViewModel()
        viewModel.login(username: "test", password: "password123")
        // TODO: 添加断言
    }
    
    func testLoginFailure() throws {
        let viewModel = LoginViewModel()
        viewModel.login(username: "", password: "")
        // TODO: 验证错误消息
    }
}
\'\'\'

    def _get_android_test_code(self) -> str:
        return \'\'\'package com.example.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AppInstrumentedTest {
    @Test
    fun loginSuccess() { /* TODO: 实现登录测试 */ }
    
    @Test
    fun loginFailure() { /* TODO: 实现登录失败测试 */ }
}
\'\'\'

'''

# 读取文件
with open('utils/agent_executor.py', 'r') as f:
    content = f.read()

# 找到插入位置（在 _get_design_spec 方法之后，测试入口之前）
insert_marker = "        return f'''# 设计规范"
insert_pos = content.find(insert_marker)

if insert_pos == -1:
    print("❌ 找不到插入位置")
    exit(1)

# 找到该方法的结束位置（''' 之后）
end_marker = "## 组件\n- 按钮：圆角 4px"
end_pos = content.find(end_marker, insert_pos)
if end_pos == -1:
    print("❌ 找不到方法结束位置")
    exit(1)

# 找到下一行开始
next_newline = content.find("'''\n\n\n# ==========", end_pos)
if next_newline == -1:
    print("❌ 找不到插入点")
    exit(1)

insert_point = next_newline + 3  # 在 ''' 之后

# 插入 Native 方法
new_content = content[:insert_point] + native_methods + content[insert_point:]

# 写回文件
with open('utils/agent_executor.py', 'w') as f:
    f.write(new_content)

print("✅ Native 方法添加完成")
