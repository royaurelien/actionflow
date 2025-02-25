# **ActionFlow**

**ActionFlow** is a Python package designed to simplify the execution of complex workflows through a structured and modular approach. By integrating powerful state management, parallel processing, and YAML-based configuration inspired by GitHub Actions, ActionFlow is ideal for orchestrating tasks in environments where flexibility, scalability, and extensibility are paramount.

---

## **Key Features**

1. **YAML Syntax Inspired by GitHub Actions**  
   Define your workflows using a familiar and intuitive YAML structure, making it easy for users already acquainted with GitHub Actions to adapt.

2. **YAML-Driven Workflows**  
   Configure your workflows, jobs, and actions in a clear, human-readable YAML format, simplifying sharing and versioning.

3. **Action Groups with Parallelism**  
   Actions are grouped based on their `concurrency` dependencies and executed in parallel or sequentially as needed, optimizing performance.

4. **Stateful Actions and Jobs**  
   Each action follows a consistent lifecycle (`_check`, `_pre_process`, `_run`, `_post_process`) with states such as `pending`, `running`, `success`, and `failed`. Jobs and groups inherit states based on their actions' outcomes.

5. **Thread-Safe Execution**  
   Execute workflows in background threads while maintaining thread safety and avoiding task collisions using a global context and locking mechanisms.

6. **CLI and Web API**  
   Run workflows, monitor logs, and check execution status using a simple CLI or a lightweight HTTP server. This makes the package versatile for both command-line and web-based integrations.

7. **Extensibility Through Python Classes**  
   Define custom actions by extending the base `Action` class. Override lifecycle methods to implement specific logic, adapting to unique requirements with ease.

8. **Efficient Resource Management**  
   Utilize multithreading and multiprocessing to handle long-running or resource-intensive tasks, such as cloning repositories or pulling Docker images.

---

## **How It Works**

### **Core Concepts**

- **Flow**: Represents the entire workflow, consisting of multiple jobs.
- **Job**: A set of grouped actions executed sequentially.
- **Action**: The building blocks of workflows, performing specific tasks and following a standardized lifecycle.

### **Example Workflow**

Define your workflow in YAML with a GitHub Actions-inspired syntax:
```yaml
name: example_flow
context:
  workspace: /tmp
  mode: test
env:
  VAR_1: value1
  VAR_2: value2
jobs:
  job1:
    steps:
      - name: action1
        with:
          concurrency: true
      - name: action2
        with:
          concurrency: true
  job2:
    steps:
      - name: action3


```

## **Getting Started with ActionFlow**

### **Installation**

You can install ActionFlow using [Poetry](https://python-poetry.org/) or pip:

```bash
pip install actionflow
```

---

### **CLI Commands**

Run your workflows directly from the command line using the following commands:

#### **Run a Workflow**

Execute a workflow defined in a YAML file:
```bash
actionflow run example.yaml
```

#### **Check Workflow Status**

Retrieve the current status of your workflow:
```bash
actionflow status
```

#### **View Logs**

Access the logs generated during workflow execution:
```bash
actionflow logs
```

---

### **Run as a Web Server**

ActionFlow can be deployed as a lightweight web server to handle workflow submissions via HTTP requests.

#### **Start the Server**

Launch the web server on a specified port:
```bash
actionflow serve --port 8080
```

#### **Submit a Workflow**

Use a `POST` request to submit a YAML workflow for processing:
```bash
curl -X POST http://localhost:8080/process -d @example.yaml -H "Content-Type: application/x-yaml"
```

#### **Retrieve Logs and Status**

- **Logs:** Fetch logs using a `GET` request:
  ```bash
  curl http://localhost:8080/logs
  ```
- **Status:** Check workflow status using a `GET` request:
  ```bash
  curl http://localhost:8080/status
  ```


## Documentation

For detailed documentation, please visit the [documentation](https://royaurelien.github.io/actionflow/).

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please contact us at support@example.com.
