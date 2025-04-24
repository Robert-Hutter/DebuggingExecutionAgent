FROM node:18-slim

# Set the timezone to avoid interactive prompts
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install git, curl, and build-essential
RUN apt-get update && apt-get install -y git curl build-essential && apt-get clean && rm -rf /var/lib/apt/lists/* || exit 0

WORKDIR /app

# Clone the repository
RUN git clone https://github.com/mermaid-js/mermaid.git || exit 0

WORKDIR /app/mermaid

# Install pnpm globally
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install --frozen-lockfile || exit 0

CMD ["bash"]